from django.contrib import admin
from .models import Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'start_date', 'end_date', 'project_type')
    list_filter = ('category', 'project_type')
    search_fields = ('name','project_type', 'category__name', 'description', 'location', 'organizer')