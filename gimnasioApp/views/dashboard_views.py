from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal
from datetime import datetime, date, timedelta
from ..serializers import MembresiasSerializer
from ..models import MembresiaAsignada, UsuarioGymDay, PagoMembresia
from ..permissions import RequirePasswordChange
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side


# ============================================================
# ESTADÍSTICAS DEL DASHBOARD (Miembros Activos, Nuevos, Retention)
# ============================================================

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated, RequirePasswordChange]
    
    def get(self, request):
        from django.db.models import Count, Q
        from datetime import date, timedelta
        
        gimnasio = request.gimnasio
        
        if not gimnasio:
            return Response({
                'active_members': 0,
                'new_today': 0,
                'retention_rate': 0
            })
        
        today = date.today()
        
        # 1. Miembros activos (membresías vigentes)
        active_memberships = MembresiaAsignada.objects.filter(
            miembro__gimnasio=gimnasio,
            dateInitial__lte=today,
            dateFinal__gte=today
        )
        active_count = active_memberships.count()
        
        # 2. Nuevos hoy (miembros que se registraronHOY)
        new_today = active_memberships.filter(
            dateInitial=today
        ).count()
        
        # 3. Retention Rate
        # Mes anterior
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        
        # Primer día del mes anterior
        prev_month_start = date(prev_year, prev_month, 1)
        
        # Último día del mes anterior
        if prev_month == 12:
            prev_month_end = date(prev_year + 1, 1, 1) - timedelta(days=1)
        else:
            prev_month_end = date(prev_year, prev_month + 1, 1) - timedelta(days=1)
        
        # Miembros únicos activos el mes anterior (distinct por miembro)
        prev_active_ids = MembresiaAsignada.objects.filter(
            miembro__gimnasio=gimnasio,
            dateInitial__lte=prev_month_end,
            dateFinal__gte=prev_month_start
        ).values_list('miembro', flat=True).distinct()
        prev_active_count = len(prev_active_ids)
        
        # De esos miembros, cuántos siguen activos hoy (con cualquier membresía)
        still_active_count = 0
        if prev_active_count > 0:
            still_active_count = MembresiaAsignada.objects.filter(
                miembro__in=list(prev_active_ids),
                miembro__gimnasio=gimnasio,
                dateFinal__gte=today,
                dateInitial__lte=today
            ).values('miembro').distinct().count()
        
        # Calcular retention
        if prev_active_count > 0:
            retention = round((still_active_count / prev_active_count) * 100, 1)
        else:
            retention = 100.0  # Si no hay miembros anteriores, 100%
        
        return Response({
            'active_members': active_count,
            'new_today': new_today,
            'retention_rate': retention
        })


# ============================================================
# HOME / DASHBOARD
# ============================================================

class Home(APIView):
    permission_classes = [IsAuthenticated, RequirePasswordChange]
    
    def get(self, request):
        gimnasio = request.gimnasio
        
        if gimnasio:
            UserGymList = MembresiaAsignada.objects.filter(miembro__gimnasio=gimnasio).order_by('-id')
            UserDayList = UsuarioGymDay.objects.filter(gimnasio=gimnasio).order_by('-id')
        else:
            UserGymList = MembresiaAsignada.objects.none()
            UserDayList = UsuarioGymDay.objects.none()

        now = timezone.now()
        month = now.month
        year = now.year

        # Mes anterior
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year

        num_miembros = UserGymList.count()

        miembrosDay_mes = UserDayList.filter(dateInitial__month=month, dateInitial__year=year)
        total_day_mes = sum(user.price for user in miembrosDay_mes)
        # Pagos recibidos este mes (dinero real, no esperado)
        pagos_mes = PagoMembresia.objects.filter(
            membresia_asignada__miembro__gimnasio=gimnasio,
            fecha_pago__month=month,
            fecha_pago__year=year
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total_month = pagos_mes + total_day_mes
        miembros_mes_count = UserGymList.filter(dateInitial__month=month, dateInitial__year=year).count()

        # Miembros del mes anterior
        miembros_mes_anterior = UserGymList.filter(
            dateInitial__month=prev_month,
            dateInitial__year=prev_year
        ).count()

        # Diferencia vs mes anterior
        diff_miembros = miembros_mes_count - miembros_mes_anterior

        total_day = sum(user.price for user in UserDayList)
        # Dinero real recibido: suma de todos los pagos de membresias + ingresos diarios
        pagos_totales = PagoMembresia.objects.filter(
            membresia_asignada__miembro__gimnasio=gimnasio
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total = pagos_totales + total_day

        # ---- Dashboard de cobranza ----
        today = date.today()
        active_memberships = UserGymList.filter(
            dateInitial__lte=today,
            dateFinal__gte=today
        )

        # Obtener total de pagos por membresia activa en una sola consulta
        pago_totals = PagoMembresia.objects.filter(
            membresia_asignada__in=active_memberships
        ).values('membresia_asignada').annotate(
            total_monto=Sum('monto')
        )
        pago_dict = {item['membresia_asignada']: item['total_monto'] for item in pago_totals}

        por_cobrar = Decimal('0')
        al_dia = 0
        con_deuda = 0

        for m in active_memberships:
            total_pagado = pago_dict.get(m.id, Decimal('0'))
            saldo = m.price - total_pagado
            if saldo > 0:
                por_cobrar += saldo
                con_deuda += 1
            else:
                al_dia += 1

        return JsonResponse({ 
            'num_miembros': num_miembros, 
            'total_month': float(total_month), 
            'miembros_mes': miembros_mes_count,
            'total': float(total),
            'miembros_mes_anterior': miembros_mes_anterior,   
            'diff_miembros': diff_miembros,
            'por_cobrar': float(por_cobrar),
            'al_dia': al_dia,
            'con_deuda': con_deuda,
        })
    


# ============================================================
# ACTIVIDADES RECIENTES
# ============================================================

class ActivitiesView(APIView):
    permission_classes = [IsAuthenticated, RequirePasswordChange]
    
    def get(self, request):
        gimnasio = request.gimnasio
        
        activities = []
        
        if gimnasio:
            membresias_recientes = MembresiaAsignada.objects.filter(
                miembro__gimnasio=gimnasio
            ).select_related('miembro', 'membresia').order_by('-created_at')[:5]

            ingresos = UsuarioGymDay.objects.filter(
                gimnasio=gimnasio
            ).order_by('-created_at')[:5]
            
            for membresia in membresias_recientes:
                
                activities.append({
                    'id': f'm-{membresia.id}',
                    'type': 'new_member',
                    'icon': 'person_add',
                    'color': 'primary',
                    'title': 'Nuevo miembro registrado',
                    'description': f'{membresia.miembro.name} {membresia.miembro.lastname} - {membresia.membresia.name}',                    
                    'created_at': membresia.created_at.isoformat(),
                    'time_ago': self.get_time_ago(membresia.created_at),
                })            
            
            
            for ingreso in ingresos:
                
                activities.append({
                    'id': f'i-{ingreso.id}',
                    'type': 'entry',
                    'icon': 'login',
                    'color': 'info',
                    'title': 'Ingreso registrado',
                    'description': f'{ingreso.name} {ingreso.lastname}',
                    'created_at': ingreso.created_at.isoformat(),
                    'amount': float(ingreso.price),
                    'time_ago': self.get_time_ago(ingreso.created_at)
                })

            # Pagos recientes (abonos o pagos completos)
            pagos_recientes = PagoMembresia.objects.filter(
                membresia_asignada__miembro__gimnasio=gimnasio
            ).select_related(
                'membresia_asignada__miembro',
                'membresia_asignada__membresia'
            ).order_by('-fecha_pago')[:5]

            for pago in pagos_recientes:
                asignacion = pago.membresia_asignada
                miembro = asignacion.miembro
                # Determinar si es pago completo o parcial
                if pago.monto >= asignacion.price:
                    tipo_pago = 'Pago completo'
                else:
                    tipo_pago = 'Abono'
                activities.append({
                    'id': f'p-{pago.id}',
                    'type': 'payment',
                    'icon': 'payments',
                    'color': 'success',
                    'title': f'{tipo_pago} - {pago.metodo_pago}',
                    'description': f'{miembro.name} {miembro.lastname} - {asignacion.membresia.name}',
                    'amount': float(pago.monto),
                    'created_at': pago.fecha_pago.isoformat(),
                    'time_ago': self.get_time_ago(pago.fecha_pago),
                })
        
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response(activities[:10])
    
     # ==========================================================
    # HELPERS
    # ==========================================================

    def ensure_datetime(self, date_obj):
        """Convierte date → datetime seguro"""
        if isinstance(date_obj, date) and not isinstance(date_obj, datetime):
            date_obj = datetime.combine(date_obj, datetime.min.time())

        if timezone.is_naive(date_obj):
            date_obj = timezone.make_aware(date_obj)

        return date_obj
    
    def get_time_ago(self, date_obj):
        now = timezone.now()
        diff = now - date_obj

        if diff.days > 0:
            return f'{diff.days} día{"s" if diff.days != 1 else ""}'
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f'{hours} hora{"s" if hours != 1 else ""}'
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f'{minutes} minuto{"s" if minutes != 1 else ""}'
        else:
            return 'Ahora mismo'
        
        
# ============================================================
# EXPORTAR REPORTE
# ============================================================

class ExportReportView(APIView):
    permission_classes = [IsAuthenticated, RequirePasswordChange]

    def get(self, request):
        gimnasio = request.gimnasio

        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"

        # ESTILOS
        header_fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        bold_font = Font(bold=True)
        center = Alignment(horizontal="center")

        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # TÍTULO
        ws.merge_cells('A1:F1')
        ws['A1'] = 'REPORTE DEL GIMNASIO'
        ws['A1'].font = Font(size=18, bold=True)
        ws['A1'].alignment = center

        ws.append([])
        ws.append([f'Generado: {timezone.now().strftime("%d/%m/%Y %H:%M")}'])
        ws.append([])

        # DATOS
        if gimnasio:
            miembros = MembresiaAsignada.objects.filter(miembro__gimnasio=gimnasio)
            diarios = UsuarioGymDay.objects.filter(gimnasio=gimnasio)
        else:
            miembros = []
            diarios = []

        total_membresias = sum(m.price for m in miembros)
        total_diarios = sum(d.price for d in diarios)
        total = total_membresias + total_diarios

        # ==========================================================
        # ESTADÍSTICAS
        # ==========================================================
        ws.append(['ESTADÍSTICAS DEL MES'])

        headers = ['Total miembros', 'Ingresos membresías', 'Ingresos diarios', 'Total']
        ws.append(headers)

        for col_num, _ in enumerate(headers, 1):
            cell = ws.cell(row=ws.max_row, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center
            cell.border = border

        ws.append([
            len(miembros),
            total_membresias,
            total_diarios,
            total
        ])

        # formato dinero
        for col in range(2, 5):
            ws.cell(row=ws.max_row, column=col).number_format = '$#,##0'

        ws.append([])

        # ==========================================================
        # 👤 MIEMBROS
        # ==========================================================
        ws.append(['MIEMBROS'])
        headers = ['Nombre', 'Apellido', 'Membresía', 'Fecha Inicio', 'Precio']
        ws.append(headers)

        for col_num, _ in enumerate(headers, 1):
            cell = ws.cell(row=ws.max_row, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border

        for m in miembros[:50]:
            ws.append([
                m.miembro.name,
                m.miembro.lastname,
                m.membresia.name,
                m.dateInitial.strftime('%d/%m/%Y'),
                m.price
            ])

            row = ws.max_row
            ws.cell(row=row, column=5).number_format = '$#,##0'

        ws.append([])

        # ==========================================================
        # INGRESOS DIARIOS
        # ==========================================================
        ws.append(['INGRESOS DIARIOS'])
        headers = ['Nombre', 'Apellido', 'Fecha', 'Monto']
        ws.append(headers)

        for col_num, _ in enumerate(headers, 1):
            cell = ws.cell(row=ws.max_row, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border

        for d in diarios[:50]:
            ws.append([
                d.name,
                d.lastname,
                d.dateInitial.strftime('%d/%m/%Y'),
                d.price
            ])

            row = ws.max_row
            ws.cell(row=row, column=4).number_format = '$#,##0'

        # ==========================================================
        # AUTO AJUSTE COLUMNAS
        # ==========================================================
        from openpyxl.utils import get_column_letter
        
        for col in ws.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                try:
                    # Ignorar celdas combinadas (MergedCell)
                    if cell.value and not isinstance(cell, type(ws.merged_cells)):
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            ws.column_dimensions[col_letter].width = max_length + 3 if max_length > 0 else 15

        # ==========================================================
        # DESCARGA
        # ==========================================================
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="reporte_gimnasio.xlsx"'

        wb.save(response)
        return response