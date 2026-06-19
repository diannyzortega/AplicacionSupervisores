import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.settings")
django.setup()

from comercial.models import RegistroDiario
import datetime

print("Total RegistroDiario records:", RegistroDiario.objects.count())

print("\nRecords for June (month=6):")
for r in RegistroDiario.objects.filter(fecha__month=6):
    print(f"- ID: {r.id}, Fecha: {r.fecha}, Asesor: {r.id_asesor}, Cat: {r.id_categoria}, Act: {r.act_dia}, Vol: {r.vol_dia}")

print("\nRecords for May (month=5):")
for r in RegistroDiario.objects.filter(fecha__month=5):
    print(f"- ID: {r.id}, Fecha: {r.fecha}, Asesor: {r.id_asesor}, Cat: {r.id_categoria}, Act: {r.act_dia}, Vol: {r.vol_dia}")
