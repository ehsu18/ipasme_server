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
import json
from collections.abc import MutableMapping


# TODO hacer bien todo el manejo de errores, mandar mensajes segun el error y manejar status 400  y 500

# TODO va a tocar que la api permita elegir cuales fields quiere que se envien, que el frontend pueda pedirlos 


'''
TODO
se podria intentar cambiar la forma en que se envian los datos en la api
puede ser:

document
basic_info {
    name    
    lastname
    fecha nacimiento
    estado civil
    sexo
}
contact_info {
    ta ta ta
}
beneficiarys {
    ta ta ta
}

asi con todas las secciones para manejar mas comodamente la
informacion y las fechas de actualizacion
'''

def affiliate(request, id=None):

    if id and request.method == 'GET':
        try:
            record = models.Affiliate.objects.get(id=ObjectId(id))
            return JsonResponse(record.get_json())
            
        except (models.Affiliate.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':
        lista = []
        for record in models.Affiliate.objects.all():
            lista.append(record.get_json())
        # print(lista)
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

            aff = models.Affiliate.objects.get(id=ObjectId(id))
            aff.modify(**data)
            aff.save()            
            return JsonResponse({'result': 'ok'})

        except (ParseError, FieldDoesNotExist,
                models.Affiliate.DoesNotExist,
                OperationError) as e:
            raise
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'POST':
        try:
            aff = models.Affiliate(**JSONParser().parse(request))
            aff.save()
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
            aff = models.Affiliate.objects.filter(id=ObjectId(id))
            aff.delete()
            return JsonResponse({'result': 'ok'})
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}, status=500)

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def affiliate_affiliates(request, id=None):
    if request.method == 'GET' and id:
        try:
            this_affiliate = models.Affiliate.objects.get(id=ObjectId(id))
            affiliates = []

            # busqueda de afiliados
            all_affiliates = models.Affiliate.objects()
            for affiliate in all_affiliates:
                for beneficiary in affiliate.beneficiarys:
                    if beneficiary.record == this_affiliate.id:
                        affiliates.append({
                            'level': beneficiary.level,
                            'record': str(affiliate.id),
                            'names': str(affiliate.names),
                            'lastnames':str(affiliate.lastnames) ,
                            'document': affiliate.document,
                            'relation_description' : 'feaure coming soon',
                            'type' : str(affiliate.type)
                        })

            return JsonResponse(affiliates, safe=False)
        except (models.Affiliate.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'})

    elif not id:  # bad request
        return JsonResponse({'error': 'bad request, id expected, must be id > 0'}, status=400)

    else:  # bad request
        return JsonResponse({'error': 'bad request'}, status=400)

def affiliate_beneficiarys(request, id=None):
    if request.method == 'POST' and id:
        try:
            dicc = JSONParser().parse(request)
            this_affiliate = models.Affiliate.objects.get(id=ObjectId(id))
            
            # checking
            for beneficiary in this_affiliate.beneficiarys:
                if str(beneficiary.record) == dicc['record']:
                    return JsonResponse({'error': 'already_exists, try with PUT to edit.'}, status=400)
            
            # adding
            beneficiary = models.Relation(level=dicc['level'], record=ObjectId(dicc['record']))
            this_affiliate.beneficiarys.append(beneficiary)
            this_affiliate.save()    
            return JsonResponse({'result': 'ok'}, safe=False)
        except (models.Affiliate.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    elif request.method == 'GET' and id:

        try:
            this_affiliate = models.Affiliate.objects.get(id=ObjectId(id))
            beneficiarys = []

            for relation in this_affiliate.beneficiarys:
                print(relation.record)
                try:
                    ben = models.Beneficiary.objects.get(id=ObjectId(relation.record))
                except Exception:
                    ben = models.Affiliate.objects.get(id=ObjectId(relation.record))
                
                beneficiarys.append({
                    'level': relation.level,
                    'record': str(relation.record),
                    'names': str(ben.names),
                    'lastnames':str(ben.lastnames) ,
                    'document': ben.document,
                    'relation_description' : 'feaure coming soon',
                    'type' : str(ben.type)
                })

            return JsonResponse(beneficiarys, safe=False)
        except (models.Affiliate.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'})    
    
    elif request.method == 'DELETE' and id:
        try:
            dicc = JSONParser().parse(request)
            this_affiliate = models.Affiliate.objects.get(id=ObjectId(id))

            # checking
            for beneficiary in this_affiliate.beneficiarys:
                if str(beneficiary.record) == dicc['record_to_delete']:
                    this_affiliate.beneficiarys.remove(beneficiary)
                    this_affiliate.save()
                    return JsonResponse({'result':'ok'})

            return JsonResponse({'error': 'that beneficiary is not in the beneficiarys list of this affiliate'}, status=400) 
        
        except (models.Affiliate.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'})    

    elif request.method == 'PUT' and id:
        try:
            dicc = JSONParser().parse(request)
            this_affiliate = models.Affiliate.objects.get(id=ObjectId(id))

            # checking
            for beneficiary in this_affiliate.beneficiarys:
                if str(beneficiary.record) == dicc['record']:
                    
                    beneficiary.level = dicc['level']

                    this_affiliate.save()
                    return JsonResponse({'result':'ok'})

            return JsonResponse({'error': 'that beneficiary is not in the beneficiarys list of this affiliate'}, status=400) 
        
        except (models.Affiliate.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}) 

    elif not id:  # bad request
        return JsonResponse({'error': 'bad request, id expected, must be id > 0'}, status=400)

    else:  # bad request
        return JsonResponse({'error': 'bad request'}, status=400)

def beneficiary(request, id=None):

    if id and request.method == 'GET':
        try:
            record = models.Beneficiary.objects.get(id=ObjectId(id))
            return JsonResponse({
                'id': str(record.id),
                'names': record.names,
                'gender': record.gender,
                'lastnames': record.lastnames,
                'document': record.document,
                'type': 'beneficiary',
            })
        except models.Beneficiary.DoesNotExist:
            return JsonResponse({'error': 'not exists'}, status=404)
        except Exception as e:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':
        lista = []
        for record in models.Beneficiary.objects.all():
            lista.append({
                'id': str(record.id),
                'names': record.names,
                'gender': record.gender,
                'lastnames': record.lastnames,
                'document': record.document,
                'type': 'beneficiary',
            })
        return JsonResponse(lista, safe=False)

    elif request.method == 'PUT' and id:
        try:
            dicc = JSONParser().parse(request)
            ben = models.Beneficiary.objects.get(id=ObjectId(id))
            ben.modify(**dicc)
            ben.save()
            return JsonResponse({'result': 'ok'})
        except FieldDoesNotExist as e:
            return JsonResponse({'error': str(e)}, status=400)
        except:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'POST':
        try:
            dicc = JSONParser().parse(request)

            doc = dicc.get('document', None)
            print(doc)
            if doc != None and models.Beneficiary.objects.filter(document=doc):
                raise NotUniqueError(f'No puede repetir el documento {doc}')

            # TODO validar document o pasarlo sin document para mantener sparse
            b = models.Beneficiary(**dicc)
            b.save()
            return JsonResponse({'result': 'ok'})
        except (TypeError, ParseError,
                IntegrityError, NotUniqueError,
                FieldDoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    elif request.method == 'DELETE' and id:
        try:
            ben = models.Beneficiary.objects.filter(id=ObjectId(id))
            if len(ben) < 1: 
                return JsonResponse({'result': 'That beneficiary does not exists.'}, status=400)
            ben.delete()
            return JsonResponse({'result': 'ok'})
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'}, status=500)

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def beneficiary_affiliates(request, id):
    if request.method == 'GET' and id:
        try:
            this_beneficiary = models.Beneficiary.objects.get(id=ObjectId(id))
            affiliates = []

            # busqueda de afiliados
            all_affiliates = models.Affiliate.objects()
            for affiliate in all_affiliates:
                for beneficiary in affiliate.beneficiarys:
                    if beneficiary.record == this_beneficiary.id:
                        affiliates.append({
                            'level': beneficiary.level,
                            'record': str(affiliate.id)
                        })

            return JsonResponse(affiliates, safe=False)
        except (models.Beneficiary.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            print(e)
            return JsonResponse({'error': 'Internal server error'})

    elif not id:  # bad request
        return JsonResponse({'error': 'bad request, id expected, must be id > 0'}, status=400)

    else:  # bad request
        return JsonResponse({'error': 'bad request'}, status=400)

def records(request, id=None):

    if id and request.method == 'GET':
        try:
            aff = affiliate(request, id)
            print(aff)
            return aff
            # if aff...
        except (models.Affiliate.DoesNotExist,
                models.Beneficiary.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)
    
    # elif ...
    
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def citas(request, record_id=None):
    if id and request.method == 'GET':
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
    
    # elif ...
    
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def citasodon(request, record_id=None):
    if id and request.method == 'GET':
        try:
            resultados = models.Citaodon.objects(record_id=record_id)
            print(resultados)
            citas = []
            for cita in resultados:
                citas.append(cita.get_json())
            return JsonResponse(citas, safe=False)
            
        except (models.CitaOdon.DoesNotExist,
                InvalidId) as e:
            # TODO los errores DoesNotExist y eso deberian estar en un nivel superior, fuera del if y usando document.DoesNotExist
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)
    
    # elif ...
    
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def affiliate_reposos(request, record_id=None):
    if record_id and request.method == 'GET':
        try:
            return JsonResponse([x.get_json() for x in models.Reposo.objects(record_id=ObjectId(record_id))], safe=False)
            
        except (models.Reposo.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':

        return JsonResponse({'error': 'bad request'}, status=400)
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def reposos(request, id=None):

    if id and request.method == 'GET':
        try:
            reposo = models.Reposo.objects.get(id=ObjectId(id))
            return JsonResponse(reposo.get_json())
            
        except (models.Reposo.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':

        return JsonResponse([x.get_json() for x in models.Reposo.objects.all()], safe=False)

    elif request.method == 'PUT' and id:
        try:
            # se puede pasar esto a una funcion
            data = JSONParser().parse(request)
            print(data)

            reposo = models.Reposo.objects.get(id=ObjectId(id))
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

    # elif request.method == 'POST':
    #     try:
    #         # TODO adaptar a la nueva api
    #         aff = models.Affiliate(**JSONParser().parse(request))
    #         aff.save()
    #         return JsonResponse({'result': 'ok'})

    #     except (TypeError, ParseError,
    #             IntegrityError, NotUniqueError) as e:
    #         return JsonResponse({'error': str(e)}, status=400)

    #     except Exception as e:
    #         # print(e)
    #         raise
    #         return JsonResponse({'error': 'bad request'}, status=400)

    # elif request.method == 'DELETE' and id:
    #     try:
    #         aff = models.Affiliate.objects.filter(id=ObjectId(id))
    #         aff.delete()
    #         return JsonResponse({'result': 'ok'})
    #     except Exception as e:
    #         print(e)
    #         return JsonResponse({'error': 'Internal server error'}, status=500)

    else:
        return JsonResponse({'error': 'bad request'}, status=400)

def affiliate_cuidos(request, record_id=None):
    if record_id and request.method == 'GET':
        try:
            return JsonResponse([x.get_json() for x in models.Cuido.objects(record_id=ObjectId(record_id))], safe=False)
            
        except (models.Cuido.DoesNotExist,
                InvalidId) as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception:
            raise
            return JsonResponse({'error': 'internal server error'}, status=500)

    elif request.method == 'GET':

        return JsonResponse({'error': 'bad request'}, status=400)
    else:
        return JsonResponse({'error': 'bad request'}, status=400)

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
            print(data)

            cuido = models.Cuido.objects.get(id=ObjectId(id))
            cuido.modify(**data)
            cuido.save()            
            return JsonResponse({'result': 'ok'})

        except (ParseError, FieldDoesNotExist,
                models.Cuido.DoesNotExist,
                OperationError) as e:
            # raise
            return JsonResponse({'error': str(e)}, status=400)

        except Exception as e:
            raise
            return JsonResponse({'error': 'bad request'}, status=400)

    else:
        return JsonResponse({'error': 'bad request'}, status=400)
