"""
DSCR Calculator Module
======================

Calculates Debt Service Coverage Ratio (DSCR) for credit analysis.

DSCR = Net Operating Income / Total Debt Service

This is a key metric for assessing a borrower's ability to repay debt.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DSCRCalculator:
    """
    Calculates and analyzes Debt Service Coverage Ratio (DSCR).

    DSCR measures the cash flow available to pay current debt obligations.
    A DSCR greater than 1.0 indicates the entity has sufficient income to
    pay its debt obligations.

    Risk Thresholds (typical banking standards):
        - Healthy: >= 1.50
        - Warning:  1.25 - 1.50
        - High Risk: < 1.25
    """

    def __init__(self, thresholds: Dict[str, float] = None):
        """
        Initialize the DSCR Calculator.

        Args:
            thresholds: Dictionary with 'healthy', 'warning', 'critical' thresholds
        """
        self.thresholds = thresholds or {
            "healthy": 1.50,
            "warning": 1.25,
            "critical": 1.0
        }

    def calculate(
        self,
        financial_data: Dict[str, Any],
        cash_flow_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Calculate DSCR from financial data.

        Args:
            financial_data: Dictionary containing financial statement data
            cash_flow_data: Optional UCA cash flow analysis results

        Returns:
            Dictionary containing DSCR calculation and risk assessment
        """
        try:
            # Get Net Operating Income (NOI)
            # Prefer cash flow data if available, otherwise use EBITDA
            if cash_flow_data and cash_flow_data.get("noi"):
                noi = cash_flow_data["noi"]
            else:
                noi = financial_data.get("ebitda", 0)

            # Calculate Total Debt Service
            interest_expense = financial_data.get("interest_expense", 0)
            principal_payment = financial_data.get("principal_payment", 0)
            total_debt_service = interest_expense + principal_payment

            # Calculate DSCR
            if total_debt_service > 0:
                dscr = noi / total_debt_service
            else:
                # No debt service = infinite coverage (but return None for clarity)
                dscr = None
                logger.info("No debt service requirement - DSCR not applicable")

            # Determine risk level
            risk_level = self._assess_risk(dscr)

            # Generate interpretation
            interpretation = self._generate_interpretation(dscr, risk_level)

            result = {
                "value": round(dscr, 4) if dscr is not None else None,
                "risk_level": risk_level,
                "interpretation": interpretation,
                "threshold_healthy": self.thresholds["healthy"],
                "threshold_warning": self.thresholds["warning"],
                "threshold_critical": self.thresholds["critical"],
                "details": {
                    "net_operating_income": round(noi, 2),
                    "interest_expense": round(interest_expense, 2),
                    "principal_payment": round(principal_payment, 2),
                    "total_debt_service": round(total_debt_service, 2)
                }
            }

            logger.debug(
                f"DSCR calculated: {dscr:.2f}x" if dscr else "DSCR: N/A (no debt service)"
            )

            return result

        except Exception as e:
            logger.error(f"Error calculating DSCR: {e}")
            return {
                "value": None,
                "risk_level": "ERROR",
                "interpretation": f"Error calculating DSCR: {str(e)}",
                "error": str(e)
            }

    def _assess_risk(self, dscr: Optional[float]) -> str:
        """
        Assess risk level based on DSCR value.

        Args:
            dscr: Calculated DSCR value

        Returns:
            Risk level string: 'LOW', 'MEDIUM', 'HIGH', or 'N/A'
        """
        if dscr is None:
            return "N/A"

        if dscr >= self.thresholds["healthy"]:
            return "LOW"
        elif dscr >= self.thresholds["warning"]:
            return "MEDIUM"
        elif dscr >= self.thresholds["critical"]:
            return "HIGH"
        else:
            return "CRITICAL"

    def _generate_interpretation(self, dscr: Optional[float], risk_level: str) -> str:
        """
        Generate human-readable interpretation of DSCR.

        Args:
            dscr: Calculated DSCR value
            risk_level: Assessed risk level

        Returns:
            Interpretation string
        """
        if dscr is None:
            return "No debt service obligation - DSCR not applicable"

        interpretations = {
            "LOW": (
                f"Strong debt service coverage at {dscr:.2f}x. "
                f"Company generates ${dscr:.2f} of NOI for every $1 of debt service. "
                "Healthy cushion for economic downturns."
            ),
            "MEDIUM": (
                f"Adequate debt service coverage at {dscr:.2f}x. "
                "Company can meet obligations but has limited cushion. "
                "Monitor closely for deterioration."
            ),
            "HIGH": (
                f"Weak debt service coverage at {dscr:.2f}x. "
                "Company has minimal cushion to absorb revenue decline. "
                "High risk of covenant violation or default."
            ),
            "CRITICAL": (
                f"Insufficient debt service coverage at {dscr:.2f}x. "
                "Company cannot fully service debt from operations. "
                "Requires additional capital or debt restructuring."
            )
        }

        return interpretations.get(risk_level, "Unable to assess DSCR")

    def calculate_minimum_noi_required(
        self,
        total_debt_service: float,
        target_dscr: float = None
    ) -> float:
        """
        Calculate the minimum NOI required to achieve target DSCR.

        Args:
            total_debt_service: Total annual debt service
            target_dscr: Target DSCR (defaults to healthy threshold)

        Returns:
            Minimum NOI required
        """
        if target_dscr is None:
            target_dscr = self.thresholds["healthy"]

        return total_debt_service * target_dscr

    def calculate_maximum_debt_service(
        self,
        noi: float,
        target_dscr: float = None
    ) -> float:
        """
        Calculate maximum debt service supported by given NOI.

        Args:
            noi: Net Operating Income
            target_dscr: Target DSCR (defaults to healthy threshold)

        Returns:
            Maximum supportable debt service
        """
        if target_dscr is None:
            target_dscr = self.thresholds["healthy"]

        if target_dscr > 0:
            return noi / target_dscr
        return 0

    def sensitivity_analysis(
        self,
        noi: float,
        total_debt_service: float,
        noi_decline_scenarios: list = None
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on DSCR under various scenarios.

        Args:
            noi: Current Net Operating Income
            total_debt_service: Total annual debt service
            noi_decline_scenarios: List of NOI decline percentages to test

        Returns:
            Dictionary with scenario analysis results
        """
        if noi_decline_scenarios is None:
            noi_decline_scenarios = [0, 5, 10, 15, 20, 25, 30]

        scenarios = []
        for decline_pct in noi_decline_scenarios:
            stressed_noi = noi * (1 - decline_pct / 100)
            stressed_dscr = (
                stressed_noi / total_debt_service
                if total_debt_service > 0
                else None
            )

            scenarios.append({
                "noi_decline_percent": decline_pct,
                "stressed_noi": round(stressed_noi, 2),
                "stressed_dscr": round(stressed_dscr, 4) if stressed_dscr else None,
                "risk_level": self._assess_risk(stressed_dscr),
                "passes_minimum": (
                    stressed_dscr >= self.thresholds["critical"]
                    if stressed_dscr
                    else True
                )
            })

        # Find breakeven point
        breakeven_noi = total_debt_service * self.thresholds["critical"]
        if noi > 0:
            breakeven_decline = ((noi - breakeven_noi) / noi) * 100
        else:
            breakeven_decline = 0

        return {
            "base_case": {
                "noi": round(noi, 2),
                "total_debt_service": round(total_debt_service, 2),
                "dscr": round(noi / total_debt_service, 4) if total_debt_service > 0 else None
            },
            "scenarios": scenarios,
            "breakeven_analysis": {
                "minimum_noi_required": round(breakeven_noi, 2),
                "maximum_noi_decline_percent": round(max(0, breakeven_decline), 2)
            }
        }
