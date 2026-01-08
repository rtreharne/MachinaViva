from django.contrib import admin
from django.apps import apps
from django.utils.safestring import mark_safe

from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "subtitle", "is_published", "published_at", "updated_at")
    list_filter = ("is_published", "published_at")
    search_fields = ("title", "subtitle", "summary", "body", "author_name")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("cover_preview",)

    fieldsets = (
        (None, {
            "fields": (
                "title",
                "subtitle",
                "slug",
                "summary",
                "body",
            )
        }),
        ("Cover image", {
            "fields": (
                "cover_image",
                "cover_preview",
                "cover_focus_x",
                "cover_focus_y",
            )
        }),
        ("Publishing", {
            "fields": (
                "author_name",
                "is_published",
                "published_at",
            )
        }),
    )

    def cover_preview(self, obj):
        if not obj.cover_image:
            return "No cover image"
        return mark_safe(f'<img src="{obj.cover_image.url}" style="max-width: 320px; height: auto;" />')

    cover_preview.short_description = "Cover preview"

    class Media:
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@6/tinymce.min.js",
            "tool/tinymce_article.js",
        )

# ---------------------------------------------------------------
# Automatically register ALL models in the 'tool' app
# ---------------------------------------------------------------

app = apps.get_app_config('tool')

for model_name, model in app.models.items():
    # Skip if already registered manually
    if admin.site.is_registered(model):
        continue

    # Create a generic ModelAdmin with sensible defaults
    class GenericAdmin(admin.ModelAdmin):
        list_display = [
            field.name for field in model._meta.fields
            if field.get_internal_type() not in ("TextField",)
        ]
        search_fields = [
            field.name for field in model._meta.fields
            if field.get_internal_type() in ("CharField", "SlugField", "TextField")
        ]
        list_filter = [
            field.name for field in model._meta.fields
            if field.get_internal_type().endswith("Field") and not field.many_to_many
            and field.get_internal_type() != "TextField"
        ]

    try:
        admin.site.register(model, GenericAdmin)
    except admin.sites.AlreadyRegistered:
        pass
