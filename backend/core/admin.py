from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(User, UserAdmin)
for model in (Role, Institution, InstitutionalFacility, Department, AcademicYear, Programme, Course, Faculty, Student,
              ResearchProject, Publication, Placement, AccreditationFramework, Criterion,
              Parameter, EvidenceDocument, Submission, Review, Notification, AuditLog):
    admin.site.register(model)
