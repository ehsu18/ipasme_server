# from django.db import models
from django.core.exceptions import ValidationError

import mongoengine as me
import re


# class User(models.Model):
#     id = models.IntegerField(
#         primary_key=True, blank=False, null=False, unique=True)
#     name = models.CharField(max_length=255)
#     lastname = models.CharField(max_length=255)
#     username = models.CharField(max_length=255)
#     password = models.CharField(max_length=255)
#     privileges = models.CharField(max_length=255)


class Relation(me.EmbeddedDocument):
    level_choices = (
        (1, "indefinido"),
        (2, 'cónyugue'),
        (3, 'hijo/hija'),
        (4, 'padre/madre'),
        (5, 'hermano/hermana')
    )
    level = me.IntField(min_value=1, max_value=5, choices=level_choices) # TODO esto esta dando un error con get_level_display, parece que no puede ser items, probar keys o usar una lista o tupla-> TypeError: 'dict_items' object is not subscriptable 
    record = me.ObjectIdField(required=True)

    def get_json(self):
        return {
            "level_code": self.level,
            "level_description" : self.get_level_display(),
            "record" : str(self.record)
        }

def document_validator(document):
    regex = re.compile(r"^\d*$")
    if not regex.match(document):
        raise ValidationError("Not a valid document, must be a number or empty")

class Record(me.Document):
   
    # TODO como se puede evitar duplicar la historia de alguien sin cedula?

    gender_options = (('M', 'masculino'), ('F','femenino'))
    nationality_options = (('V','Venezolano'), ('E', 'Extranjero'))
    civilstatus_options = ('Soltero', 'Casado', 'Viudo', 'Divorciado')
    job_status_options = ('Activo', 'Reposo', 'Jubilado', 'Inactivo') # TODO revisar cuales hay
    type_options = ('affiliate', 'beneficiary')

    type = me.StringField(max_length=255, choices=type_options)  

    document = me.StringField(required=True, unique=True, validation=document_validator)
    names = me.StringField(max_length=255)
    lastnames = me.StringField(max_length=255)
    gender = me.StringField(max_length=255, choices=gender_options)
    nationality = me.StringField(max_length=255, choices=nationality_options)
    dateofbirth = me.DateTimeField(default=None) 
    civilstatus = me.StringField(max_length=255, choices=civilstatus_options)
    placeofbirth = me.StringField(max_length=255)

    # datos de contacto
    phone_personal = me.StringField(max_length=255)
    phone_optional = me.StringField(max_length=255)
    home_direction = me.StringField(max_length=255)
    email = me.StringField(max_length=255)

    # datos medicos
    rh_group = me.StringField(max_length=255)
    enfermedades_hereditarias = me.StringField(max_length=255)
    enfermedades_cronicas = me.StringField(max_length=255)
    alergias = me.StringField(max_length=255)
    # es abstract por lo de los index pero hay que ver si se puede cambiar

    # datos odontologicos
    odon_folder = me.StringField()
    odon_padecimientos = me.StringField()
    odon_procedimientos = me.StringField()

    #datos laborales
    job_name = me.StringField(max_length=255)
    job_status = me.StringField(max_length=255, choices=job_status_options)
    job_title = me.StringField(max_length=255)
    job_direction = me.StringField(max_length=255)

    beneficiarys = me.EmbeddedDocumentListField(Relation)
    # Beneficiary, through="AffiliateToBeneficiary")
    # TODO al eliminar un afiliado no se debe borrar sus beneficiarios sino
    # revisar si no tienen mas afiliados, en ese caso borrar.
    # TODO creo que el numero deberia ser str y  permitir "+"
    meta = {
        "indexes": [
            {
                'fields': ['document'],
                'unique': True,
                'sparse': True
            }
        ]
    }

    @property
    def nationality_display(self):
        return self.nationality_options[self.nationality]
    
    def get_json(self):
        return {
            
            'type':self.type,
            'id':str(self.id),
            'basic_info' : {
                'document': self.document,
                'names' : self.names,
                'lastnames' : self.lastnames,
                'gender' : self.gender,
                'nationality' : self.nationality, 
                'dateofbirth' : self.dateofbirth, 
                'civilstatus' : self.civilstatus,
                'placeofbirth' : self.placeofbirth
            } ,
            'contact_info' : {
                'phone_personal':self.phone_personal,
                'phone_optional':self.phone_optional,
                'home_direction':self.home_direction,
                'email' : self.email
            } ,
            'job_info' : {
                'job_name' : self.job_name,
                'job_status':self.job_status,
                'job_title':self.job_title,
                'job_direction':self.job_direction
            } ,
            'medic_info' : {
                'rh_group':self.rh_group,
                'enfermedades_hereditarias':self.enfermedades_hereditarias,
                'enfermedades_cronicas':self.enfermedades_cronicas,
                'alergias':self.alergias
            } ,
            "odon_info" : {
                "odon_folder" : self.odon_folder,
                "odon_padecimientos" : self.odon_padecimientos,
                "odon_procedimientos" : self.odon_procedimientos
            } 
            #"beneficiarys" : [r.get_json() for r in self.beneficiarys] 
        }


class Reposo(me.Document):
    
    record_id = me.ReferenceField(Record, reverse_delete_rule=me.CASCADE) 
    fecha_inicio = me.DateTimeField(default=None)
    fecha_fin = me.DateTimeField(default=None)
    dias = me.IntField()
    otorgado = me.StringField()
    conformado = me.StringField()
    medico = me.StringField()
    especialidad = me.StringField()
    total_reposo = me.IntField()
    total_dias = me.IntField()

    def get_json(self):
        return {
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "dias": self.dias,
            "otorgado" : self.otorgado,
            "conformado" : self.conformado,
            "medico":self.medico,
            "especialidad":self.especialidad,
            "total_reposo":self.total_reposo,
            "total_dias":self.total_dias,
            "record_id":str(self.record_id)
            # supongo que tenga un id o un index
        }
    

class Cita(me.Document):

    record_id = me.ReferenceField(Record, reverse_delete_rule=me.CASCADE) 
    names=me.StringField()
    lastnames = me.StringField()
    age=me.IntField()
    document=me.StringField()
    phone=me.StringField()
    gender=me.StringField()
    tipo=me.StringField()
    job_type = me.StringField()
    area = me.StringField()
    fecha = me.DateTimeField(default=None)
    record_type = me.StringField()
    first_cita = me.BooleanField()
    tension_arterial = me.StringField()
    peso = me.FloatField()
    estudio_lab = me.BooleanField()
    estudio_rx = me.BooleanField()
    estudio_eco = me.BooleanField()
    reposo = me.IntField()
    ref = me.BooleanField()
    diagnose = me.StringField()

    def get_json(self):
        return {
            "id": str(self.id),
            "record_id": str(self.record_id),
            "area" : self.area,
            "fecha": self.fecha,
            "age": self.age,
            "record_type": self.record_type,
            "first_cita": self.first_cita,
            "tension_arterial": self.tension_arterial,
            "peso": self.peso,
            "estudio_lab": self.estudio_lab,
            "estudio_rx": self.estudio_rx,
            "estudio_eco": self.estudio_eco,
            "reposo": self.reposo,
            "ref": self.ref,
            "diagnose" : self.diagnose
            }

class Citaodon(me.Document):
    record_id = me.ReferenceField(Record, reverse_delete_rule=me.CASCADE) 
    age = me.IntField()
    fecha = me.DateTimeField(default=None)
    record_type = me.StringField()
    first_cita = me.BooleanField()
    reposo = me.IntField()
    ref = me.BooleanField()
    diagnose = me.StringField()

    def get_json(self):
        return {
            "id": str(self.id),
            "record_id": str(self.record_id),
            "fecha": self.fecha,
            "age": self.age,
            "record_type": self.record_type,
            "first_cita": self.first_cita,
            "reposo": self.reposo,
            "ref": self.ref,
            "diagnose" : self.diagnose
            }

class Cuido(me.Document):
    
    record_id = me.ReferenceField(Record, reverse_delete_rule=me.CASCADE)
    fecha_inicio = me.DateTimeField(default=None)
    fecha_fin = me.DateTimeField(default=None)
    dias = me.IntField()
    beneficiary = me.StringField()
    beneficiary_name = me.StringField()
    beneficiary_id = me.StringField(default=None) 
    beneficiary_type = me.StringField()
    reason = me.StringField()

    total_cuido = me.IntField()
    total_dias = me.IntField()

    def get_json(self):
        return {
            "fecha_inicio": self.fecha_inicio,
            "fecha_fin": self.fecha_fin,
            "dias": self.dias,
            "beneficiary": self.beneficiary,
            "beneficiary_name" : self.beneficiary_id,
            "beneficiary_id" : self.beneficiary_id,
            "beneficiary_type" : self.beneficiary_type,
            "reason" : self.reason,
            "total_cuido":self.total_cuido,
            "total_dias":self.total_dias,
            "record_id":str(self.record_id)
            # supongo que tenga un id o un index
        }
  
