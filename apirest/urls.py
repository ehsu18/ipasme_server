from django.urls import path, register_converter
from . import views

urlpatterns = [    
    path('affiliate', views.affiliate), 
    path('affiliate/<str:id>', views.affiliate),
    path('affiliate_affiliates/<str:id>', views.affiliate_affiliates),
    path('affiliate_beneficiarys/<str:id>', views.affiliate_beneficiarys),

    path('beneficiary', views.beneficiary),
    path('beneficiary/<str:id>', views.beneficiary),
    path('beneficiary_affiliates/<str:id>', views.beneficiary_affiliates),

    # path('relations/affiliate_beneficiary', views.affiliate_beneficiary_relations),
    # path('relations/affiliate_beneficiary/<int:id>', views.affiliate_beneficiary_relations),
    # # path('relations/affiliate_affiliate/<int:id>', viewss.affiliate_affiliate_relations),
    # TODO crear records
    # path('records', views.records)
]