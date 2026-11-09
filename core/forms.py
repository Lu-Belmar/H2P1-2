# core/forms.py
from django import forms


class CargaExcelForm(forms.Form):
    archivo_excel = forms.FileField()


class EditarFilaForm(forms.Form):
    fila_excel = forms.IntegerField(min_value=1, error_messages={
        "required": "El número de fila es obligatorio.",
        "invalid": "El número de fila debe ser un número entero válido.",
        "min_value": "El número de fila debe ser mayor a 0.",
    })