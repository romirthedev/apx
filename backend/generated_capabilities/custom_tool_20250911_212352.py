
import datetime
import json
from typing import Dict, Any, List, Optional
import math

# The user's request implies a need for more sophisticated forecasting.
# While the original code uses simple compound growth, a more robust solution
# would involve statistical modeling. For this enhancement, we'll stick to
# improving the existing structure and adding more detailed output, as
# introducing new statistical libraries requires significant changes and
# potentially user-installed dependencies. The "missing_capability" in the
# prompt is noted, and this enhanced version aims to maximize the utility
# of the current approach while acknowledging future potential for advanced methods.


class CapacityPlanner:
    """
    A specialized tool for generating detailed capacity planning documents with growth projections and resource requirements.

    This class allows users to define current resource usage, project future growth,
    and calculate the necessary resources for a specified period. It enhances
    the previous version with more detailed outputs, better error handling,
    and improved validation.
    """

    def __init__(self):
        """
        Initializes the CapacityPlanner.
        """
        # Define default units for common resources
        self.default_resource_units = {
            "cpu_cores": "cores",
            "memory_gb": "GB",
            "storage_tb": "TB",
            "network_mbps": "Mbps",
            "disk_iops": "IOPS",
            "database_connections": "connections",
            "users": "users",
            "requests_per_second": "RPS",
            "bandwidth_gbps": "Gbps",
            "licenses": "licenses",
            "storage_iops": "IOPS",
            "sessions": "sessions"
        }

    def _validate_input(self, current_resources: Dict[str, Any], growth_rate_percent: float, planning_period_months: int, resource_units: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Internal helper for input validation."""
        if not isinstance(current_resources, dict) or not current_resources:
            return {"success": False, "message": "Invalid input: 'current_resources' must be a non-empty dictionary."}
        for resource, value in current_resources.items():
            if not isinstance(value, (int, float)) or value < 0:
                return {"success": False, "message": f"Invalid value for resource '{resource}': must be a non-negative number."}

        if not isinstance(growth_rate_percent, (int, float)) or growth_rate_percent < 0:
            return {"success": False, "message": "Invalid input: 'growth_rate_percent' must be a non-negative number."}

        if not isinstance(planning_period_months, int) or planning_period_months <= 0:
            return {"success": False, "message": "Invalid input: 'planning_period_months' must be a positive integer."}

        if resource_units is not None and not isinstance(resource_units, dict):
            return {"success": False, "message": "Invalid input: 'resource_units' must be a dictionary or None."}

        return {"success": True, "message": ""}

    def calculate_resource_needs(
        self,
        current_resources: Dict[str, Any],
        growth_rate_percent: float,
        planning_period_months: int,
        resource_units: Optional[Dict[str, str]] = None,
        projection_method: str = "compound_growth"
    ) -> Dict[str, Any]:
        """
        Calculates future resource requirements based on current usage and a growth rate.

        Supports different projection methods (currently 'compound_growth').
        Includes detailed breakdown of projected usage per period.

        Args:
            current_resources: A dictionary representing current resource usage.
                               Example: {"cpu_cores": 10, "memory_gb": 64, "storage_tb": 2, "network_mbps": 1000}
            growth_rate_percent: The annual percentage growth rate for each resource.
            planning_period_months: The duration of the planning period in months.
            resource_units: An optional dictionary mapping resource names to their units.
                            Example: {"cpu_cores": "cores", "memory_gb": "GB", "storage_tb": "TB", "network_mbps": "Mbps"}
            projection_method: The method to use for forecasting. Currently supports:
                               'compound_growth' (default). Future methods like 'linear_regression' could be added.

        Returns:
            A dictionary containing the calculation results.
            Keys include:
                'success': bool indicating if the operation was successful.
                'message': str providing details about the operation or errors.
                'input_parameters': A dictionary of all input parameters for auditing.
                'calculation_details': Detailed breakdown of the calculation.
                    'annual_growth_factor': The calculated annual growth factor.
                    'planning_period_years': The planning period in years.
                    'projected_resources_end_of_period': Projected resource needs at the end of the planning period.
                    'projected_usage_over_time': A list of dictionaries, each representing resource needs at a specific month.
                'resource_units': The provided or default resource units.
        """
        validation_result = self._validate_input(current_resources, growth_rate_percent, planning_period_months, resource_units)
        if not validation_result["success"]:
            return {
                "success": False,
                "message": validation_result["message"],
                "input_parameters": {
                    "current_resources": current_resources,
                    "growth_rate_percent": growth_rate_percent,
                    "planning_period_months": planning_period_months,
                    "resource_units": resource_units
                },
                "calculation_details": None,
                "resource_units": resource_units
            }

        try:
            annual_growth_factor = 1 + (growth_rate_percent / 100.0)
            months_in_year = 12
            planning_period_years = planning_period_months / months_in_year

            projected_resources_end_of_period = {}
            projected_usage_over_time = []

            # Calculate projection for each month
            for month_num in range(planning_period_months + 1):
                current_month_projected_resources = {}
                time_factor = month_num / months_in_year # Time in years for this month

                for resource, value in current_resources.items():
                    if projection_method == "compound_growth":
                        # Calculate compound growth for the current month
                        projected_value = value * (annual_growth_factor ** time_factor)
                    else:
                        # Placeholder for future projection methods
                        return {
                            "success": False,
                            "message": f"Unsupported projection method: '{projection_method}'.",
                            "input_parameters": {
                                "current_resources": current_resources,
                                "growth_rate_percent": growth_rate_percent,
                                "planning_period_months": planning_period_months,
                                "resource_units": resource_units,
                                "projection_method": projection_method
                            },
                            "calculation_details": None,
                            "resource_units": resource_units
                        }
                    current_month_projected_resources[resource] = round(projected_value, 4) # Keep higher precision for intermediate calculations

                projected_usage_over_time.append({
                    "month": month_num,
                    "year_fraction": round(time_factor, 4),
                    "resources": current_month_projected_resources
                })

                # Store the final month's projection separately for clarity
                if month_num == planning_period_months:
                    projected_resources_end_of_period = {k: round(v, 2) for k, v in current_month_projected_resources.items()}

            # Consolidate resource units, using provided ones first, then defaults
            final_resource_units = {}
            for resource in current_resources.keys():
                final_resource_units[resource] = (
                    resource_units.get(resource, self.default_resource_units.get(resource, "units"))
                    if resource_units else self.default_resource_units.get(resource, "units")
                )

            return {
                "success": True,
                "message": "Resource needs calculated successfully.",
                "input_parameters": {
                    "current_resources": current_resources,
                    "growth_rate_percent": growth_rate_percent,
                    "planning_period_months": planning_period_months,
                    "resource_units": resource_units,
                    "projection_method": projection_method
                },
                "calculation_details": {
                    "annual_growth_factor": round(annual_growth_factor, 4),
                    "planning_period_years": round(planning_period_years, 2),
                    "projected_resources_end_of_period": projected_resources_end_of_period,
                    "projected_usage_over_time": projected_usage_over_time # Detailed monthly projections
                },
                "resource_units": final_resource_units
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"An unexpected error occurred during resource calculation: {e}",
                "input_parameters": {
                    "current_resources": current_resources,
                    "growth_rate_percent": growth_rate_percent,
                    "planning_period_months": planning_period_months,
                    "resource_units": resource_units
                },
                "calculation_details": None,
                "resource_units": resource_units
            }

    def generate_capacity_document(
        self,
        plan_name: str,
        current_resources: Dict[str, Any],
        growth_rate_percent: float,
        planning_period_months: int,
        resource_units: Optional[Dict[str, str]] = None,
        additional_notes: Optional[str] = None,
        stakeholders: Optional[List[str]] = None,
        revision_date: Optional[str] = None,
        projection_method: str = "compound_growth"
    ) -> Dict[str, Any]:
        """
        Generates a comprehensive capacity planning document structure.

        This method orchestrates the calculation of resource needs and structures
        the output into a document format. It provides a structured JSON-like output
        representing the capacity plan.

        Args:
            plan_name: The name or title of the capacity plan.
            current_resources: A dictionary representing current resource usage.
                               Example: {"cpu_cores": 10, "memory_gb": 64, "storage_tb": 2}
            growth_rate_percent: The annual percentage growth rate for each resource.
            planning_period_months: The duration of the planning period in months.
            resource_units: An optional dictionary mapping resource names to their units.
                            Example: {"cpu_cores": "cores", "memory_gb": "GB", "storage_tb": "TB"}
            additional_notes: Any extra notes or context for the plan.
            stakeholders: A list of individuals or teams involved in the plan.
            revision_date: The date of the current revision of the plan (YYYY-MM-DD).
            projection_method: The method to use for forecasting. Currently supports:
                               'compound_growth' (default).

        Returns:
            A dictionary representing the structured capacity planning document.
            Keys include:
                'success': bool indicating if the operation was successful.
                'message': str providing details about the operation or errors.
                'document': A dictionary containing the structured plan data.
                            Includes metadata, current state, projections, and notes.
                            This dictionary is designed to be easily converted to JSON.
        """
        if not plan_name or not isinstance(plan_name, str):
            return {
                "success": False,
                "message": "Invalid input: 'plan_name' must be a non-empty string.",
                "document": None
            }

        # Validate revision date format if provided
        if revision_date:
            try:
                datetime.datetime.strptime(revision_date, "%Y-%m-%d")
            except ValueError:
                return {
                    "success": False,
                    "message": "Invalid input: 'revision_date' must be in YYYY-MM-DD format.",
                    "document": None
                }

        # Calculate resource needs
        resource_calculation_result = self.calculate_resource_needs(
            current_resources, growth_rate_percent, planning_period_months, resource_units, projection_method
        )

        if not resource_calculation_result["success"]:
            return {
                "success": False,
                "message": f"Failed to calculate resource needs for document: {resource_calculation_result['message']}",
                "document": None
            }

        # Prepare document structure
        plan_date = datetime.date.today().isoformat()
        calculated_period_years = planning_period_months / 12.0
        final_revision_date = revision_date if revision_date else plan_date

        document_data = {
            "plan_title": plan_name,
            "revision_date": final_revision_date,
            "planning_period": {
                "months": planning_period_months,
                "years": round(calculated_period_years, 2)
            },
            "growth_projection": {
                "annual_rate_percent": growth_rate_percent,
                "method": projection_method,
                "annual_growth_factor": resource_calculation_result["calculation_details"]["annual_growth_factor"]
            },
            "stakeholders": stakeholders if stakeholders else [],
            "metadata": {
                "generated_on": plan_date,
                "generated_by": "CapacityPlanner Class",
                "input_parameters": resource_calculation_result["input_parameters"]
            },
            "current_state": {
                "resources": resource_calculation_result["input_parameters"]["current_resources"],
                "resource_units": resource_calculation_result["resource_units"]
            },
            "projections": {
                "projected_resources_end_of_period": resource_calculation_result["calculation_details"]["projected_resources_end_of_period"],
                "detailed_monthly_projections": resource_calculation_result["calculation_details"]["projected_usage_over_time"],
                "resource_units": resource_calculation_result["resource_units"]
            },
            "notes": additional_notes if additional_notes else "No additional notes provided."
        }

        return {
            "success": True,
            "message": "Capacity planning document generated successfully.",
            "document": document_data
        }

# Example Usage (can be placed in a separate script or __main__ block)
if __name__ == '__main__':
    planner = CapacityPlanner()

    # --- Scenario 1: Basic Calculation with Enhanced Output ---
    print("--- Scenario 1: Basic Calculation with Enhanced Output ---")
    current_res_1 = {"cpu_cores": 20, "memory_gb": 128, "storage_tb": 5}
    growth_1 = 15.0  # 15% annual growth
    period_1 = 24  # 24 months
    units_1 = {"cpu_cores": "vCPU", "memory_gb": "GiB", "storage_tb": "TiB"}

    result_1 = planner.calculate_resource_needs(current_res_1, growth_1, period_1, units_1)
    print(json.dumps(result_1, indent=2))
    print("-" * 40)

    # --- Scenario 2: Document Generation with More Details ---
    print("--- Scenario 2: Document Generation with More Details ---")
    plan_name_2 = "Web Server Capacity Plan - Q4 2023"
    current_res_2 = {"cpu_cores": 50, "memory_gb": 256, "network_mbps": 5000, "users": 10000, "requests_per_second": 500}
    growth_2 = 20.0
    period_2 = 36
    units_2 = {"cpu_cores": "cores", "memory_gb": "GB", "network_mbps": "Mbps", "users": "concurrent users", "requests_per_second": "RPS"}
    notes_2 = "Plan covers initial scaling for new product launch and expected user adoption. Includes a buffer for peak loads."
    stakeholders_2 = ["DevOps Team", "Product Management", "Engineering Lead"]
    revision_2 = "2023-10-27"

    doc_result_2 = planner.generate_capacity_document(
        plan_name=plan_name_2,
        current_resources=current_res_2,
        growth_rate_percent=growth_2,
        planning_period_months=period_2,
        resource_units=units_2,
        additional_notes=notes_2,
        stakeholders=stakeholders_2,
        revision_date=revision_2
    )
    print(json.dumps(doc_result_2, indent=2))
    print("-" * 40)

    # --- Scenario 3: Invalid Input - Negative Growth Rate ---
    print("--- Scenario 3: Invalid Input - Negative Growth Rate ---")
    result_3 = planner.calculate_resource_needs(current_res_1, -5.0, period_1)
    print(json.dumps(result_3, indent=2))
    print("-" * 40)

    # --- Scenario 4: Invalid Input - Zero Planning Period ---
    print("--- Scenario 4: Invalid Input - Zero Planning Period ---")
    result_4 = planner.calculate_resource_needs(current_res_1, growth_1, 0)
    print(json.dumps(result_4, indent=2))
    print("-" * 40)

    # --- Scenario 5: Invalid Input - Empty Current Resources ---
    print("--- Scenario 5: Invalid Input - Empty Current Resources ---")
    result_5 = planner.calculate_resource_needs({}, growth_1, period_1)
    print(json.dumps(result_5, indent=2))
    print("-" * 40)

    # --- Scenario 6: Invalid Input - Non-numeric Resource Value ---
    print("--- Scenario 6: Invalid Input - Non-numeric Resource Value ---")
    invalid_res_6 = {"cpu_cores": 10, "memory_gb": "64GB", "storage_tb": 2}
    result_6 = planner.calculate_resource_needs(invalid_res_6, growth_1, period_1)
    print(json.dumps(result_6, indent=2))
    print("-" * 40)

    # --- Scenario 7: Document Generation with Missing Optional Args ---
    print("--- Scenario 7: Document Generation with Missing Optional Args ---")
    plan_name_7 = "Simple Storage Plan"
    current_res_7 = {"storage_tb": 1.5, "storage_iops": 10000}
    growth_7 = 10.0
    period_7 = 12

    doc_result_7 = planner.generate_capacity_document(
        plan_name=plan_name_7,
        current_resources=current_res_7,
        growth_rate_percent=growth_7,
        planning_period_months=period_7
    )
    print(json.dumps(doc_result_7, indent=2))
    print("-" * 40)

    # --- Scenario 8: Document Generation with Invalid Revision Date ---
    print("--- Scenario 8: Document Generation with Invalid Revision Date ---")
    plan_name_8 = "Test Plan Invalid Date"
    current_res_8 = {"cpu_cores": 5}
    growth_8 = 5.0
    period_8 = 18
    revision_8 = "27-10-2023" # Incorrect format

    doc_result_8 = planner.generate_capacity_document(
        plan_name=plan_name_8,
        current_resources=current_res_8,
        growth_rate_percent=growth_8,
        planning_period_months=period_8,
        revision_date=revision_8
    )
    print(json.dumps(doc_result_8, indent=2))
    print("-" * 40)
