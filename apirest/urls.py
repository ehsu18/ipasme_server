from django.urls import path, register_converter
from . import views

urlpatterns = [    
    path('record', views.record), 
    path('record/<str:id>', views.record),
    path('record_affiliates/<str:affiliate_id>', views.record_affiliates),
    path('record_beneficiarys/<str:affiliate_id>', views.record_beneficiarys),
    path('create_affiliate', views.create_affiliate), 
    path('create_beneficiary/<str:affiliate_id>', views.create_beneficiary),
    path("filter_affiliates/<str:text>", views.filter_affiliates),
    path("filter_affiliates", views.filter_affiliates),
    path("filter_records/<str:text>", views.filter_records),
    path("filter_records", views.filter_records),


    path('citas/<str:record_id>', views.citas),
    path('citasodon/<str:record_id>', views.citasodon),

    path("reposos", views.reposos),
    path("reposos/<str:id>", views.reposos),
    path("search_reposos/<str:record_id>", views.search_reposos),
    path("cuidos", views.cuidos),
    path("cuidos/<str:id>", views.cuidos),
    path("search_cuidos/<str:record_id>", views.search_cuidos),
]