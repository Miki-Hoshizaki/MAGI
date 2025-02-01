from django.contrib import admin
from .models import Task, Vote


# Register your models here.

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('request_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('request_id', 'original_request', 'generated_content')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('task', 'voter_id', 'result', 'created_at')
    list_filter = ('result', 'created_at')
    search_fields = ('voter_id', 'reason')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
