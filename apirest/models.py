# from django.db import models
# from django.core.exceptions import ValidationError

import mongoengine as me
import datetime


# class User(models.Model):
#     id = models.IntegerField(
#         primary_key=True, blank=False, null=False, unique=True)
#     name = models.CharField(max_length=255)
#     lastname = models.CharField(max_length=255)
#     username = models.CharField(max_length=255)
#     password = models.CharField(max_length=255)
#     privileges = models.CharField(max_length=255)


class Relation(me.EmbeddedDocument):
    level_choices = {
        1: "indefinido",
        2: 'cónyugue',
        3: 'hijo/hija',
        4: 'padre/madre',
        5: 'hermano/hermana'
    }
    level = me.IntField(min_value=1, max_value=5, choices=level_choices.keys())
    record = me.ObjectIdField(required=True)


class Record(me.Document):
    '''This is a base model for all records, containing
    fields that are used in affiliate and beneficiary'''
    # TODO implementar un auto serialize/json
    # creo que no es necesario poner id
    # id = me.IntField(primary_key=True, unique=True, )
    nationality_options = (('V','Venezolano'), ('E', 'Extranjero'))
    civilstatus_options = ('Soltero', 'Casado', 'Viudo', 'Divorciado')
    gender_options = (('M', 'masculino'), ('F','femenino'))


    names = me.StringField(max_length=255)
    lastnames = me.StringField(max_length=255)
    gender = me.StringField(max_length=255, choices=gender_options)
    nationality = me.StringField(max_length=255, choices=nationality_options)
    dateofbirth = me.DateTimeField(default=None) # TODO convertir a fecha el la API
    civilstatus = me.StringField(max_length=255, choices=civilstatus_options)
    placeofbirth = me.StringField(max_length=255)
    # personaldata_last_mod_date = me.DateField(default=datetime.datetime.utcnow)

    # datos de contacto
    phone_personal = me.StringField(max_length=255)
    phone_optional = me.StringField(max_length=255)
    home_direction = me.StringField(max_length=255)

    # es abstract por lo de los index pero hay que ver si se puede cambiar
    meta = {'abstract': True}

    # meta data
    # class Meta:
    #     abstract = True

    @property
    def nationality_display(self):
        return self.nationality_options[self.nationality]


class Beneficiary(Record):
    # hay que validar document como unique pero que ignore null
    # https://www.mongodb.com/community/forums/t/cant-create-a-unique-index-that-ignores-nulls-in-mongodb/199145/6
    # respuesta! -> https://stackoverflow.com/questions/7955040/mongodb-mongoose-unique-if-not-null
    # mientras, hay que filtrarlo en vista
    document = me.IntField()
    type = me.StringField(max_length=255, default='beneficiary')
    # TODO no va a tener affiliate pero se debe comprobar en view si tiene afiliado o no antes de editar
    meta = {
        "indexes": [
            {
                'fields': ['document'],
                'unique': True,
                'sparse': True
            }
        ]
    }

class Affiliate(Record):
    # hereda id y todo eso de Record
    # TODO ordenar todo para que sea mas legible
    jobstatus_options = ('Activo', 'Reposo', 'Jubilado', 'Inactivo') # TODO revisar cuales hay

    document = me.IntField(required=True, unique=True)
    type = me.StringField(max_length=255, default='affiliate')

    #datos laborales
    job_status = me.StringField(max_length=255)
    job_title = me.StringField(max_length=255)
    job_direction = me.StringField(max_length=255)

    beneficiarys = me.EmbeddedDocumentListField(Relation)
    #     Beneficiary, through="AffiliateToBeneficiary")

    meta = {
        "indexes": [
            {
                'fields': ['document'],
                'unique': True
            }
        ]
    }
