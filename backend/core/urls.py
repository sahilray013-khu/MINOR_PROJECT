from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet)
router.register('institutions', views.InstitutionViewSet)
router.register('departments', views.DepartmentViewSet)
router.register('academic-years', views.AcademicYearViewSet)
router.register('facilities', views.InstitutionalFacilityViewSet)
router.register('programmes', views.ProgrammeViewSet)
router.register('courses', views.CourseViewSet)
router.register('faculty', views.FacultyViewSet)
router.register('students', views.StudentViewSet)
router.register('research-projects', views.ResearchProjectViewSet)
router.register('publications', views.PublicationViewSet)
router.register('placements', views.PlacementViewSet)
router.register('frameworks', views.FrameworkViewSet)
router.register('criteria', views.CriterionViewSet)
router.register('parameters', views.ParameterViewSet)
router.register('evidence', views.EvidenceViewSet)
router.register('submissions', views.SubmissionViewSet)
router.register('notifications', views.NotificationViewSet, basename='notification')
router.register('audit', views.AuditLogViewSet)

urlpatterns = [
    path('bulk-import/<slug:resource>/template/', views.BulkImportView.as_view()),
    path('bulk-import/<slug:resource>/', views.BulkImportView.as_view()),
    path('health/', views.health),
    path('auth/me/', views.me),
    path('auth/profile/', views.update_profile),
    path('auth/change-password/', views.change_password),
    path('auth/register/', views.register),
    path('auth/student-options/', views.student_registration_options),
    path('auth/student-register/', views.student_register),
    path('auth/student-profile/', views.student_profile),
    path('dashboard/', views.dashboard),
    path('report-download/', views.report_download),
    path('', include(router.urls)),
]
