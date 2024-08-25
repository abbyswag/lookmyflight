from rest_framework import permissions

class IsAgentOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow agents to view, edit, or delete their own bookings,
    and create new bookings.
    """

    def has_permission(self, request, view):
        # Agents can create new bookings
        if request.user.groups.filter(name='agent').exists() and request.method == 'POST':
            return True
        # Agents can only view their own bookings
        elif request.user.groups.filter(name='agent').exists() and request.method in permissions.SAFE_METHODS:
            return True
        # Supervisors have full permissions
        elif request.user.groups.filter(name='supervisor').exists():
            return True
        else:
            return False

    def has_object_permission(self, request, view, obj):
        # Agents can only view, edit, or delete their own bookings
        if request.user.groups.filter(name='agent').exists():
            if request.method in permissions.SAFE_METHODS:
                return obj.added_by == request.user
            else:
                return obj.added_by == request.user
        # Supervisors have full permissions
        elif request.user.groups.filter(name='supervisor').exists():
            return True
        else:
            return False

class IsSupervisor(permissions.BasePermission):
    """
    Custom permission to allow supervisors to perform any action on bookings.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name='supervisor').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='supervisor').exists()