# excelapp/views.py
from django.shortcuts import render, redirect
from .forms import ExcelFileForm
from .processing import process_excel
from django.http import HttpResponse

def result_file(request):
    return render(request, 'excelapp/result.html')

def index(request):
    #return render(request, 'excelapp/index.html')
    if request.method == 'POST':
        form = ExcelFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.save()
            # Llama a la función de procesamiento y obtén el resultado
            result = process_excel(excel_file.file.path)
            return render(request, 'excelapp/result.html', {'table': result})
    else:
        form = ExcelFileForm()
    return render(request, 'excelapp/index.html', {'form': form})

