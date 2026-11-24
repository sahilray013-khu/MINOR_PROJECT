from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Submission, EvidenceDocument, Department, Faculty, Student, AuditLog


@receiver(post_save, sender=Submission)
def submission_audit(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.submitted_by,
            action='CREATED',
            module='SUBMISSIONS',
            record_reference=str(instance.pk),
            change_details={'status': instance.status, 'title': instance.title},
        )
    else:
        AuditLog.objects.create(
            user=instance.submitted_by,
            action='MODIFIED',
            module='SUBMISSIONS',
            record_reference=str(instance.pk),
            change_details={'status': instance.status, 'title': instance.title},
        )


@receiver(post_save, sender=EvidenceDocument)
def evidence_audit(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.uploaded_by,
            action='UPLOADED',
            module='EVIDENCE',
            record_reference=str(instance.pk),
            change_details={'title': instance.title, 'version': instance.version},
        )


@receiver(post_save, sender=Department)
@receiver(post_save, sender=Faculty)
@receiver(post_save, sender=Student)
def record_audit(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            action='CREATED',
            module=sender.__name__.upper(),
            record_reference=str(instance.pk),
            change_details={'name': str(instance)},
        )


@receiver(post_delete, sender=Submission)
@receiver(post_delete, sender=EvidenceDocument)
@receiver(post_delete, sender=Department)
@receiver(post_delete, sender=Faculty)
@receiver(post_delete, sender=Student)
def deletion_audit(sender, instance, **kwargs):
    AuditLog.objects.create(
        action='DELETED',
        module=sender.__name__.upper(),
        record_reference=str(instance.pk),
        change_details={'name': str(instance)},
    )
