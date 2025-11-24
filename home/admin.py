from django.contrib import admin
from .models import AdminIndex, CarouselSlide, AdminAbout, AdminInstitutionalManagement, AdminBom, AdminAcDpt,AdminNonAcDpt, Department, Course, Trainee, AdminCredentials, TraineeSession, Timetable, Session, TrainerOtherDocument

class CarouselSlideInline(admin.TabularInline):
    model = CarouselSlide
    extra = 1
    fields = ('image', 'heading', 'subheading', 'order')
    can_delete = True
    ordering = ['order']

@admin.register(AdminIndex)
class AdminIndexAdmin(admin.ModelAdmin):
    list_display = ('num_institutions', 'num_trainees', 'num_trainers', 'updated_at')
    inlines = [CarouselSlideInline]

@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ('admin_index', 'heading', 'subheading', 'order')
    search_fields = ['heading', 'subheading']
    ordering = ['order']


@admin.register(AdminAbout)
class AdminAboutAdmin(admin.ModelAdmin):
    list_display = ['title', 'phone']

@admin.register(AdminInstitutionalManagement)
class AdminAdminInstitutionalManagement(admin.ModelAdmin):
    list_display = ['title', 'name']

@admin.register(AdminBom)
class AdminBomAdmin(admin.ModelAdmin):
    list_display = ['title', 'name']

@admin.register(AdminAcDpt)
class AdminAcDptAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(AdminNonAcDpt)
class AdminNonAcDptAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'level', 'date_registered', 'term1_fees', 'term2_fees', 'term3_fees', 'total_fees')
    list_filter = ('department',)

@admin.register(Trainee)
class TraineeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'trainee_number', 'course', 'date_of_admission')
    search_fields = ('first_name', 'last_name', 'trainee_number', 'course__name')
    list_filter = ( 'course', 'department')
    readonly_fields = ('trainee_number',)

@admin.register(AdminCredentials)
class AdminCredentialsAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'designation', 'staff_number')
    search_fields = ('username', 'name', 'staff_number')

@admin.register(TraineeSession)
class TraineeSessionAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'year_of_study', 'term', 'fee_balance', 'session_period', 'date_registered')
    list_filter = ('year_of_study', 'term', 'date_registered', )
    search_fields = ('trainee__trainee_number', 'trainee__name')


from .models import CurrentSession, TrainerData

@admin.register(CurrentSession)
class CurrentSessionAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'is_active', 'session_period')
    list_filter = ('is_active', 'start_date', 'end_date', 'session_period')
    search_fields = ('is_active',)


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'level', 'start_date', 'end_date')
    list_filter = ('course', 'level')
    search_fields = ('name', 'course__name')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)
    filter_horizontal = ()
    

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'timetable', 'session_type', 'start_time', 'location')
    list_filter = ('timetable', 'session_type', 'start_time')
    search_fields = ('title', 'timetable__name', 'location')
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)    
    
@admin.register(TrainerData)
class TrainerDataAdmin(admin.ModelAdmin):    
    list_display = ('first_name', 'last_name',  'department')
    search_fields = ('first_name', 'last_name', 'department__name')
    list_filter = ('department',)

@admin.register(TrainerOtherDocument)
class TrainerOtherDocumentAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'document')
    search_fields = ('trainer', 'document')
    list_filter = ('trainer', 'document')