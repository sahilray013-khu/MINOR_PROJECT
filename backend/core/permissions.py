from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_admin(user):
    return user.is_authenticated and user.role in ('SUPER_ADMIN', 'INSTITUTIONAL_ADMIN')


class CanManageRecords(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated or request.user.role == 'STUDENT':
            return False
        if request.method in SAFE_METHODS:
            return True
        if is_admin(request.user):
            return True
        if request.user.role in (
            'ACCREDITATION_COORDINATOR', 'DEPARTMENT_ADMIN',
            'FACULTY_STAFF', 'REVIEWER_VERIFIER',
        ):
            return True
        return False


class IsManagementOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated
