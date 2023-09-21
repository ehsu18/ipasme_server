from django.http import JsonResponse, HttpResponse
# from django.core.exceptions import ValidationError #FieldDoesNotExist
from . import models
# from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.exceptions import ParseError
from django.db.utils import IntegrityError

from mongoengine.errors import NotUniqueError, FieldDoesNotExist, OperationError
from bson import ObjectId
from bson.errors import InvalidId
from collections.abc import MutableMapping


from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response as RestResponse
from rest_framework import status

from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token

from .serializers import UserSerializer

# TODO hacer bien todo el manejo de errores, mandar mensajes segun el error y manejar status 400  y 500

# TODO va a tocar que la api permita elegir cuales fields quiere que se envien, que el frontend pueda pedirlos 

# TODO se debe revisar el resultado de las operaciones en base de datos
# para corroborar los resultados y no retornar un ok por defecto sino
# basado en lo que diga la base de datos
@api_view(['POST'])
def login(request):
    user = get_object_or_404(User, username=request.data['username'])
    if not user.check_password(request.data['password']):
        return RestResponse("missing user", status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(user)
    return RestResponse({'token': token.key, 'user': serializer.data})

# @api_view(['POST'])
# def signup(request):
#     serializer = UserSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         user = User.objects.get(username=request.data['username'])
#         user.set_password(request.data['password'])
#         user.save()
#         token = Token.objects.create(user=user)
#         return RestResponse({'token': token.key, 'user': serializer.data})
#     return RestResponse(serializer.errors, status=status.HTTP_200_OK)

# @api_view(['GET'])
# @authentication_classes([SessionAuthentication, TokenAuthentication])
# @permission_classes([IsAuthenticated])
# def test_token(request):
#     return RestResponse("passed!")

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def record(request, id=None):

    if id and request.method == 'GET':
        try:
            record = models.Record.objects.get(id=ObjectId(id))
            return JsonResponse(record.get_json())
            
        except (models.Record.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':
        lista = [r.get_json() for r in models.Record.objects.order_by('+names')] # TODO aqui se puede usar agregation o hacer un @property en el modelo
        return JsonResponse(lista, safe=False)

    elif request.method == 'PUT' and id:
        try:
            # se puede pasar esto a una funcion
            dic = JSONParser().parse(request)
            print(dic)
            data = {}
            for k,v in dic.items():
                if isinstance(v, MutableMapping):
                    data.update(v)
                    # TODO aqui se debe agregar el elemento de la fecha
                else:
                    data[k]=v

            aff = models.Record.objects.get(id=ObjectId(id))
            aff.modify(**data)
            aff.save()            
            return JsonResponse({'result': 'ok'})
        
        except (ParseError, FieldDoesNotExist,
                OperationError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        except (models.Record.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=404)

        except Exception as e:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'POST':
        return JsonResponse({'error':'You can\'t add a record with this endpoint. You must use create_affiliate or create_beneficiary'}, status=400)

    elif request.method == 'DELETE' and id:
        try:
            # TODO falta algun tipo de validacion o no se
            # TODO cuando se borran los records hay que borrarlos de las listas de beneficiarys

            del_record = models.Record.objects.get(id=ObjectId(id))

 
            for i in del_record.beneficiarys:
                # si el beneficiario tiene menos de dos afiliados se suma 1
                if models.Record.objects(beneficiarys__record=i.record).count() == 1:
                    try:
                        beneficiary = models.Record.objects(id=i.record)
                        beneficiary.delete()
                    except:
                        raise

            for aff in models.Record.objects(beneficiarys__record=ObjectId(id)):
                aff.beneficiarys = list(filter(lambda b: b.record != id ,aff.beneficiarys)) # TODO esto da un filter object, no una lista
                aff.save()

            del_record.delete()
            return JsonResponse({'result': 'ok'})


        except Exception as e:
            raise

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def record_affiliates(request, affiliate_id=None):
    if request.method == 'GET' and affiliate_id:
        try:
            record = models.Record.objects.get(id=ObjectId(affiliate_id))
            result = []

            # busqueda de afiliados
            affiliates = models.Record.objects(type='affiliate')

            for affiliate in affiliates:
                for relation in affiliate.beneficiarys:
                    if relation.record == record.id:
                        result.append({
                            'level_code': relation.level,
                            'level_description':relation.get_level_display(),
                            'record': str(affiliate.id),
                            'names': affiliate.names,
                            'lastnames':affiliate.lastnames,
                            'document': affiliate.document,
                            'nationality' : affiliate.nationality,
                            'type' : str(affiliate.type)
                        })

            return JsonResponse(result, safe=False)
        
        except (models.Record.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=404)
        
        except Exception as e:
            raise

    else:  # bad request
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def record_beneficiarys(request, affiliate_id=None):
    if request.method == 'POST' and affiliate_id:
        try:
            json = JSONParser().parse(request)
            # TODO si es beneficiary no va a tener beneficiarios
            try:
                affiliate = models.Record.objects.get(id=ObjectId(affiliate_id))
                if affiliate.type != 'affiliate': return JsonResponse({'error': 'affiliate_id is not an affiliate'}, status=400)
            except models.Record.DoesNotExist as e :
                return JsonResponse({'error': str(e)}, status=400)
            
            try:
                beneficiary = models.Record.objects.get(id=ObjectId(json['record']))
            except models.Record.DoesNotExist as e :
                return JsonResponse({'error': str(e)}, status=400)
            

            # checking if relation exist
            if [r for r in affiliate.beneficiarys if r.record == beneficiary.id]:
                return JsonResponse({'error': 'relation already_exists, try with PUT to edit.'}, status=400)
            
            # adding
            relation = models.Relation(level=json['level'], record=beneficiary.id)
            affiliate.beneficiarys.append(relation)
            affiliate.save()    
            return JsonResponse({'result': 'ok'}, safe=False)

        except (TypeError, ParseError, IntegrityError) as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        except Exception as e:
            raise
    
    elif request.method == 'GET' and affiliate_id:

        try:
            affiliate = models.Record.objects.get(id=ObjectId(affiliate_id))
            if affiliate.type != 'affiliate': return JsonResponse([], safe=False) # si no es afiliado no tiene beneficiarios

            relations = []
            for r in affiliate.beneficiarys:
                try:
                    ben = models.Record.objects.get(id=r.record) 
                    relations.append({ #TODO se podria mejorar este json, pero habria que cambiar el frontend
                        'names': ben.names,
                        'lastnames':ben.lastnames,
                        'document': ben.document,
                        'type' : ben.type,
                        'record': str(r.record),
                        'level_code': r.level,
                        'level_description':r.get_level_display(),
                        'dateofbirth':ben.dateofbirth,
                        'id':str(ben.id),
                        'nationality':ben.nationality,

                    })
                
                    # aqui viene cuando no existe el beneficiario al que se hace referencia, se deberia borrar aqui mismo de la lista
                    # AUTO PURGUE
                except models.Record.DoesNotExist as e:
                    affiliate.beneficiarys.remove(r)
                    affiliate.save()
                    print(e)
                except Exception as e:
                    print(e)

                    
            return JsonResponse(relations, safe=False)
        except (models.Record.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            raise   
    
    elif request.method == 'DELETE' and affiliate_id:
        try:
            json = JSONParser().parse(request)
            print(json)

            if models.Record.objects(beneficiarys__record=json['beneficiary']).count() <= 1:
                return JsonResponse({'error': 'unique affiliate'})

            affiliate = models.Record.objects.get(id=ObjectId(affiliate_id))
            if affiliate.type != 'affiliate': return JsonResponse({'error': 'affiliate_id is not an affiliate'}, status=400)

            # checking
            relation = affiliate.beneficiarys.get(record = json['beneficiary'])
            if relation:
                affiliate.beneficiarys.remove(relation)
                affiliate.save()
                return JsonResponse({'result':'ok'})
            else:
                return JsonResponse({'error': 'not in the beneficiarys list'}, status=404) 
        
        except (models.Record.DoesNotExist) as e:
            return JsonResponse({'error': 'does not exist'}, status=404)
        except Exception as e:
            raise   

    elif request.method == 'PUT' and affiliate_id:
        try:
            json = JSONParser().parse(request)
            print(json)
            affiliate = models.Record.objects.get(id=ObjectId(affiliate_id))

            # checking
            for relation in affiliate.beneficiarys:
                if str(relation.record) == json['record']:
                    
                    relation.level = json['level']

                    affiliate.save()
                    return JsonResponse({'result':'ok'})

            return JsonResponse({'error': 'that beneficiary is not in the beneficiarys list of this affiliate'}, status=404) 
        
        except models.Record.DoesNotExist as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            raise 

    else:  # bad request
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_affiliate(request):
    try:
        datos = JSONParser().parse(request)

        new_record = models.Record(**datos, type='affiliate')
        #TODO ceudla
        new_record.save()
        return JsonResponse({'result': 'ok'})

    except (NotUniqueError):
        return JsonResponse({'error': 'Document already exists'}, status=400)

    except (TypeError, ParseError,
            IntegrityError) as e:
        return JsonResponse({'error': str(e)}, status=400)

    except Exception as e:
        raise

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_beneficiary(request, affiliate_id=None):
    try:
        aff = models.Record.objects.get(id=ObjectId(affiliate_id))
        if aff.type != 'affiliate': return JsonResponse({'error': 'affiliate_id is not an affiliate'}, status=400)
        json = JSONParser().parse(request) # TODO revisar si el parse no se repite tambien en otros lados

        new_record = models.Record(**json['record_data'], type='beneficiary')
        new_record.save() # TODO probar a poner esto de ultimo para evitar guardar si hubo un fallo, sino no importa
        rel = models.Relation(level=int(json['relation_data']['level']),
                              record=new_record.id)
        aff.beneficiarys.append(rel)
        aff.save()    
        return JsonResponse({'result': 'ok'})

    except (models.Record.DoesNotExist) as e:
        print('affiliate does not exist')
        return JsonResponse({'error': 'affiliate does not exist'}, status=400)

    except (NotUniqueError):
        print('Document already exists')
        return JsonResponse({'error': 'Document already exists'}, status=400)

    except (TypeError, ParseError,
            IntegrityError) as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=400)

    except Exception as e:
        raise

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def filter_affiliates(request, text=''):
    if not text: return JsonResponse([], safe=False) 
    try:
        by_names = set(models.Record.objects(type='affiliate', names__icontains = text).only('names', 'lastnames', 'id', 'document', 'nationality').order_by('+names')[:5])
        by_lastnames = set(models.Record.objects(type='affiliate', lastnames__icontains = text).only('names', 'lastnames', 'id', 'document', 'nationality').order_by('+names')[:5])
        by_document = set(models.Record.objects(type='affiliate', document__icontains = text).only('names', 'lastnames', 'id', 'document', 'nationality').order_by('+names')[:5])
        result = set(by_names | by_document | by_lastnames)
        
        return JsonResponse([{
            'names':x.names, 'lastnames':x.lastnames, 'id':str(x.id), 'document':x.document, 'nationality':x.nationality
            } for x in result], safe=False)
    # except (TypeError, ParseError,
    #         IntegrityError) as e:
    #     return JsonResponse({'error': str(e)}, status=400)

    except Exception as e:
        raise

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def filter_records(request, text=''):
    if not text: return JsonResponse([], safe=False) 
    try:
        by_names = set(models.Record.objects(names__icontains = text).only('names', 'lastnames', 'id', 'document', 'nationality').order_by('+names')[:5])
        by_lastnames = set(models.Record.objects(lastnames__icontains = text).only('names', 'lastnames', 'id', 'document', 'nationality').order_by('+names')[:5])
        by_document = set(models.Record.objects(document__icontains = text).only('names', 'lastnames', 'id', 'document', 'nationality').order_by('+names')[:5])
        result = set(by_names | by_document | by_lastnames)
        print(result)
        return JsonResponse([{
            'names':x.names, 'lastnames':x.lastnames, 'id':str(x.id), 'document':x.document, 'nationality':x.nationality
            } for x in result], safe=False)
    # except (TypeError, ParseError,
    #         IntegrityError) as e:
    #     return JsonResponse({'error': str(e)}, status=400)

    except Exception as e:
        raise

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def record_citas(request, record_id=None):
    if record_id and request.method == 'GET':
        try:
            resultados = models.Cita.objects(record_id=record_id)
            print(resultados)
            citas = []
            for cita in resultados:
                citas.append(cita.get_json())
            return JsonResponse(citas, safe=False)
            
        except (models.Cita.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def citas(request, cita_id=None):
    if request.method ==  'GET' and cita_id:
        try:
            cita = models.Cita.objects.get(id=ObjectId(cita_id))
            return JsonResponse(cita.get_json(), safe=False)
        except (models.Cita.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': 'Does not exist'}, status=404)
        except:
            raise
    elif request.method ==  'POST':
        try:
            json = JSONParser().parse(request)
            print(json)
            cita = models.Cita(**json)
            cita.save()
            return JsonResponse({'result':'ok', 'cita_id':str(cita.id)})
        except:
            raise
    elif request.method ==  'PUT' and cita_id:
        try:
            cita = models.Cita.objects.get(id=ObjectId(cita_id))
            json = JSONParser().parse(request)
            cita.modify(**json)
            cita.save()
            return JsonResponse({'result':'ok'})
        except (models.Cita.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': 'Does not exist'}, status=404)
        except (TypeError, ParseError,
            IntegrityError) as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=400)
        except:
            raise
    elif request.method ==  'DELETE' and cita_id:
        try:
            cita = models.Cita.objects.get(id=ObjectId(cita_id))
            cita.delete()
            return JsonResponse({'result':'ok'})
        except (models.Cita.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': 'Does not exist'}, status=404)
        except:
            raise
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def record_citasodon(request, record_id=None):
    if record_id and request.method == 'GET':
        try:
            resultados = models.Citaodon.objects(record_id=record_id)
            print(resultados)
            citas = []
            for cita in resultados:
                citas.append(cita.get_json())
            return JsonResponse(citas, safe=False)
            
        except (models.Citaodon.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def citasodon(request, citaodon_id=None):
    if request.method ==  'GET' and citaodon_id:
        try:
            citaodon = models.Citaodon.objects.get(id=ObjectId(citaodon_id))
            return JsonResponse(citaodon.get_json(), safe=False)
        except (models.Citaodon.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': 'Does not exist'}, status=404)
        except:
            raise
    elif request.method ==  'POST':
        try:
            json = JSONParser().parse(request)
            citaodon = models.Citaodon(**json)
            citaodon.save()
            return JsonResponse({'result':'ok', 'citaodon_id':str(citaodon.id)})
        except:
            raise
    elif request.method ==  'PUT' and citaodon_id:
        try:
            citaodon = models.Citaodon.objects.get(id=ObjectId(citaodon_id))
            json = JSONParser().parse(request)
            print(json)
            citaodon.modify(**json)
            citaodon.save()
            return JsonResponse({'result':'ok'})
        except (models.Citaodon.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': 'Does not exist'}, status=404)
        except (TypeError, ParseError,
            IntegrityError) as e:
            print(e)
            return JsonResponse({'error': str(e)}, status=400)
        except:
            raise
    elif request.method ==  'DELETE' and citaodon_id:
        try:
            citaodon = models.Citaodon.objects.get(id=ObjectId(citaodon_id))
            citaodon.delete()
            return JsonResponse({'result':'ok'})
        except (models.Cita.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': 'Does not exist'}, status=404)
        except:
            raise
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_reposos(request, record_id=None):
    if record_id and request.method == 'GET':
        try:
            return JsonResponse([x.get_json() for x in models.Reposo.objects(record_id=ObjectId(record_id))], safe=False)
        except Exception:
            raise

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def reposos(request, reposo_id=None):

    if reposo_id and request.method == 'GET':
        try:
            reposo = models.Reposo.objects.get(id=ObjectId(reposo_id))
            return JsonResponse(reposo.get_json())
            
        except (models.Reposo.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':

        return JsonResponse([x.get_json() for x in models.Reposo.objects.all()], safe=False)

    elif request.method == 'PUT' and reposo_id:
        try:
            # se puede pasar esto a una funcion
            data = JSONParser().parse(request)
            print(data)

            reposo = models.Reposo.objects.get(id=ObjectId(reposo_id))
            reposo.modify(**data)
            reposo.save()            
            return JsonResponse({'result': 'ok'})

        except (ParseError, FieldDoesNotExist,
                models.Reposo.DoesNotExist,
                OperationError) as e:
            # raise
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'POST':
        try:
            # TODO adaptar a la nueva api
            reposo = models.Reposo(**JSONParser().parse(request))
            reposo.save()
            return JsonResponse({'result': 'ok'})

        except (TypeError, ParseError,
                IntegrityError, NotUniqueError) as e:
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            # print(e)
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'DELETE' and reposo_id:
        try:
            reposo = models.Reposo.objects.filter(id=ObjectId(reposo_id))
            reposo.delete()
            return JsonResponse({'result': 'ok'})
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}, status=500)

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_cuidos(request, record_id=None):
    if record_id and request.method == 'GET':
        try:
            return JsonResponse([x.get_json() for x in models.Cuido.objects(record_id=ObjectId(record_id))], safe=False)
        except Exception:
            raise

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def cuidos(request, id=None):

    if id and request.method == 'GET':
        try:
            cuido = models.Cuido.objects.get(id=ObjectId(id))
            return JsonResponse(cuido.get_json())
            
        except (models.Cuido.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':

        return JsonResponse([x.get_json() for x in models.Cuido.objects.all()], safe=False)

    elif request.method == 'PUT' and id:
        try:
            # se puede pasar esto a una funcion
            data = JSONParser().parse(request)

            cuido = models.Cuido.objects.get(id=ObjectId(id))
            cuido.modify(**data)
            cuido.save()            
            return JsonResponse({'result': 'ok'})

        except (ParseError, FieldDoesNotExist,
                models.Cuido.DoesNotExist,
                OperationError) as e:
            # raise
            return JsonResponse({'error': str(e)}, status=404)

        except Exception as e:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'POST':
        try:
            cuido = models.Cuido(**JSONParser().parse(request))
            cuido.save()
            return JsonResponse({'result': 'ok'})

        except (TypeError, ParseError,
                IntegrityError, NotUniqueError) as e:
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            # print(e)
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'DELETE' and id:
        try:
            reposo = models.Cuido.objects.filter(id=ObjectId(id))
            reposo.delete()
            return JsonResponse({'result': 'ok'})
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}, status=500)


    else:
        return JsonResponse({'error': 'bad request'}, status=400)

@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def record_count(request):
    return JsonResponse({
        'records':models.Record.objects().count(),
        'affiliates':models.Record.objects(type='affiliate').count(),
        'beneficiarys':models.Record.objects(type='beneficiary').count()
    })

@api_view(['GET', 'PUT', 'POST', 'DELETE'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def informes(request, informe_id=None):
    if informe_id and request.method == 'GET':
        try:
            return JsonResponse(models.Informe.objects.get(id=ObjectId(informe_id)).get_json())
        except (models.Informe.DoesNotExist, InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)

    elif request.method == 'GET':
        return JsonResponse([x.get_json() for x in
                             models.Informe.objects().all()], safe=False)
    elif request.method == 'POST':
        try:
            informe = models.Informe(**JSONParser().parse(request))
            informe.save()

            return JsonResponse({'result': 'ok', 'informe_id':str(informe.id)})

        except (TypeError, ParseError,
                IntegrityError, NotUniqueError) as e:
            return JsonResponse({'error': str(e)}, status=400)
    elif request.method == 'PUT' and informe_id:
        try:
            # se puede pasar esto a una funcion
            data = JSONParser().parse(request)

            informe = models.Informe.objects.get(id=ObjectId(informe_id))
            informe.modify(**data)
            informe.save()            
            return JsonResponse({'result': 'ok'})

        except (ParseError, FieldDoesNotExist,
                models.Informe.DoesNotExist,
                OperationError) as e:
            # raise
            return JsonResponse({'error': str(e)}, status=404)

    elif request.method == 'DELETE' and informe_id:
        try:
            informe = models.Informe.objects.filter(id=ObjectId(informe_id))
            informe.delete()
            return JsonResponse({'result': 'ok'})
        except (models.Informe.DoesNotExist, InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}, status=500)

    else:
        return JsonResponse({'error': 'bad request'}, status=400)
    
@api_view(['GET'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_informe_citas(request, informe_id=None):
    if informe_id and request.method == 'GET':
        try:
            citas = [x.get_json() for x in models.Cita.objects(informe=ObjectId(informe_id))]
            # TODO agregar citas odon
            return JsonResponse(citas, safe=False)
        except Exception:
            raise

    else:
        return JsonResponse({'error': 'bad request'}, status=400)