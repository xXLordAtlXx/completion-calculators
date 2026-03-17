
from dataclasses import dataclass


@dataclass
class SafetyValveInput:
    tvd_ft: float
    control_fluid_ppg: float
    valve_opening_pressure_psi: float
    available_surface_pressure_psi: float
    friction_loss_psi: float = 0.0


def ppg_to_psi_per_ft(ppg: float) -> float:
    return 0.052 * ppg


def hydrostatic_pressure(depth_ft: float, gradient_psi_per_ft: float) -> float:
    return depth_ft * gradient_psi_per_ft


def calculate_control_line_hydrostatic(tvd_ft: float, control_fluid_ppg: float) -> float:
    gradient = ppg_to_psi_per_ft(control_fluid_ppg)
    return hydrostatic_pressure(tvd_ft, gradient)


def calculate_downhole_control_pressure(
    surface_pressure_psi: float,
    hydrostatic_psi: float,
    friction_loss_psi: float = 0.0
) -> float:
    return surface_pressure_psi + hydrostatic_psi - friction_loss_psi


def calculate_required_surface_pressure(
    valve_opening_pressure_psi: float,
    hydrostatic_psi: float,
    friction_loss_psi: float = 0.0
) -> float:
    return valve_opening_pressure_psi - hydrostatic_psi + friction_loss_psi


def calculate_operating_margin(
    available_surface_pressure_psi: float,
    required_surface_pressure_psi: float
) -> float:
    return available_surface_pressure_psi - required_surface_pressure_psi


def validate_inputs(data: SafetyValveInput) -> list:
    errors = []

    if data.tvd_ft < 0:
        errors.append("La TVD no puede ser negativa.")

    if data.control_fluid_ppg <= 0:
        errors.append("La densidad del fluido de control debe ser mayor que cero.")

    if data.valve_opening_pressure_psi < 0:
        errors.append("La presión de apertura no puede ser negativa.")

    if data.available_surface_pressure_psi < 0:
        errors.append("La presión disponible en superficie no puede ser negativa.")

    if data.friction_loss_psi < 0:
        errors.append("La pérdida por fricción no puede ser negativa.")

    return errors


def evaluate_safety_valve_operation(data: SafetyValveInput) -> dict:
    errors = validate_inputs(data)
    if errors:
        return {"errors": errors}

    gradient = ppg_to_psi_per_ft(data.control_fluid_ppg)

    hydrostatic_psi = calculate_control_line_hydrostatic(
        data.tvd_ft,
        data.control_fluid_ppg
    )

    required_surface_pressure_psi = calculate_required_surface_pressure(
        data.valve_opening_pressure_psi,
        hydrostatic_psi,
        data.friction_loss_psi
    )

    downhole_pressure_with_available_surface = calculate_downhole_control_pressure(
        data.available_surface_pressure_psi,
        hydrostatic_psi,
        data.friction_loss_psi
    )

    margin_psi = calculate_operating_margin(
        data.available_surface_pressure_psi,
        required_surface_pressure_psi
    )

    can_open = downhole_pressure_with_available_surface >= data.valve_opening_pressure_psi

    return {
        "errors": [],
        "tvd_ft": data.tvd_ft,
        "control_fluid_ppg": data.control_fluid_ppg,
        "control_fluid_gradient_psi_per_ft": gradient,
        "hydrostatic_pressure_psi": hydrostatic_psi,
        "valve_opening_pressure_required_downhole_psi": data.valve_opening_pressure_psi,
        "friction_loss_psi": data.friction_loss_psi,
        "required_surface_pressure_psi": required_surface_pressure_psi,
        "available_surface_pressure_psi": data.available_surface_pressure_psi,
        "downhole_pressure_with_available_surface_psi": downhole_pressure_with_available_surface,
        "operating_margin_psi": margin_psi,
        "can_open_valve": can_open
    }
