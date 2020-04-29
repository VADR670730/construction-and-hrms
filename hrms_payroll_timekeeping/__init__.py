from . import models
from . import wizard

# OT Formula
# daily_wage = (contract.wage * 12) / float(contract.resource_calendar_id.year_days)
# rendered_ot_hours = sum(i.rendered_hours if i.code == 'OT' else 0 for i in payslip.employee_attendance_summary.overtime_ids)
# result = ((daily_wage / 8) * 1.30) * rendered_ot_hours
#

# Allowance Prorated
# year_days = float(contract.resource_calendar_id.year_days)
# cutoff_type = contract.cutoff_template_id.cutoff_type
# multiplier = 1
# if cutoff_type == 'bi-monthly':
#     multiplier = 2
#
# if cutoff_type != 'weekly':
#     daily_rate = ((inputs.RAS and inputs.RAS.amount * multiplier) * 12) / year_days
# else: daily_rate = (inputs.RAS and inputs.RAS.amount * 52) / year_days
#
# allowance = inputs.RAS and inputs.RAS.amount- (daily_rate * payslip.employee_attendance_summary.total_absent)
# result = allowance > 0 and allowance or 0

# WTAX
# taxable_amount = sum([rules.BASIC and BASIC or 0.0, rules.OT and OT or 0.0, rules.OTND and OTND or 0.0])
# result = contract.compute_wtax(payslip, 'WTAX', taxable_amount)


# SSS
# result = contract.compute_sss(payslip, categories.GROSS, "EE", "SSSEE", "GROSS")
