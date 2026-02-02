"""
Leverage Ratio Analysis Module
==============================

Calculates and analyzes key leverage ratios for credit analysis:
- Debt-to-Equity Ratio
- Debt-to-EBITDA Ratio
- Interest Coverage Ratio
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class LeverageRatioAnalyzer:
    """
    Analyzes leverage ratios for credit assessment.

    Key Ratios:
        1. Debt-to-Equity: Total Debt / Total Equity
           - Measures financial leverage and risk
           - Lower is generally better

        2. Debt-to-EBITDA: Total Debt / EBITDA
           - Measures ability to pay off debt
           - Number of years to pay off debt at current EBITDA

        3. Interest Coverage: EBITDA / Interest Expense
           - Measures ability to pay interest obligations
           - Higher is better
    """

    def __init__(self, thresholds: Dict[str, Dict[str, float]] = None):
        """
        Initialize the Leverage Ratio Analyzer.

        Args:
            thresholds: Dictionary of thresholds for each ratio
        """
        self.thresholds = thresholds or {
            "debt_to_equity": {
                "healthy": 1.0,
                "warning": 2.0,
                "critical": 3.0
            },
            "debt_to_ebitda": {
                "healthy": 3.0,
                "warning": 4.0,
                "critical": 5.0
            },
            "interest_coverage": {
                "healthy": 3.0,
                "warning": 2.0,
                "critical": 1.5
            }
        }

    def analyze(self, financial_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate all leverage ratios for the given financial data.

        Args:
            financial_data: Dictionary containing financial statement data

        Returns:
            Dictionary containing all leverage ratio calculations
        """
        return {
            "debt_to_equity": self.calculate_debt_to_equity(financial_data),
            "debt_to_ebitda": self.calculate_debt_to_ebitda(financial_data),
            "interest_coverage": self.calculate_interest_coverage(financial_data)
        }

    def calculate_debt_to_equity(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Debt-to-Equity ratio.

        Formula: Total Debt / Total Equity

        Args:
            financial_data: Dictionary containing financial statement data

        Returns:
            Dictionary with ratio value and risk assessment
        """
        try:
            total_debt = financial_data.get("total_debt", 0)
            total_equity = financial_data.get("total_equity", 0)

            if total_equity > 0:
                ratio = total_debt / total_equity
            elif total_equity == 0 and total_debt > 0:
                ratio = float("inf")
            else:
                ratio = 0

            thresholds = self.thresholds["debt_to_equity"]
            risk_level = self._assess_ratio_risk(
                ratio,
                thresholds,
                lower_is_better=True
            )

            interpretation = self._interpret_debt_to_equity(ratio, risk_level)

            return {
                "value": round(ratio, 4) if ratio != float("inf") else None,
                "risk_level": risk_level,
                "interpretation": interpretation,
                "threshold_healthy": thresholds["healthy"],
                "threshold_warning": thresholds["warning"],
                "threshold_critical": thresholds["critical"],
                "details": {
                    "total_debt": round(total_debt, 2),
                    "total_equity": round(total_equity, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating Debt-to-Equity: {e}")
            return self._error_result("debt_to_equity", str(e))

    def calculate_debt_to_ebitda(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Debt-to-EBITDA ratio.

        Formula: Total Debt / EBITDA
        Represents the number of years needed to pay off debt at current EBITDA.

        Args:
            financial_data: Dictionary containing financial statement data

        Returns:
            Dictionary with ratio value and risk assessment
        """
        try:
            total_debt = financial_data.get("total_debt", 0)
            ebitda = financial_data.get("ebitda", 0)

            if ebitda > 0:
                ratio = total_debt / ebitda
            elif ebitda <= 0 and total_debt > 0:
                ratio = float("inf")
            else:
                ratio = 0

            thresholds = self.thresholds["debt_to_ebitda"]
            risk_level = self._assess_ratio_risk(
                ratio,
                thresholds,
                lower_is_better=True
            )

            interpretation = self._interpret_debt_to_ebitda(ratio, risk_level)

            return {
                "value": round(ratio, 4) if ratio != float("inf") else None,
                "risk_level": risk_level,
                "interpretation": interpretation,
                "threshold_healthy": thresholds["healthy"],
                "threshold_warning": thresholds["warning"],
                "threshold_critical": thresholds["critical"],
                "details": {
                    "total_debt": round(total_debt, 2),
                    "ebitda": round(ebitda, 2),
                    "years_to_payoff": (
                        f"{ratio:.1f} years" if ratio != float("inf") else "N/A"
                    )
                }
            }

        except Exception as e:
            logger.error(f"Error calculating Debt-to-EBITDA: {e}")
            return self._error_result("debt_to_ebitda", str(e))

    def calculate_interest_coverage(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Interest Coverage ratio (Times Interest Earned).

        Formula: EBITDA / Interest Expense

        Args:
            financial_data: Dictionary containing financial statement data

        Returns:
            Dictionary with ratio value and risk assessment
        """
        try:
            ebitda = financial_data.get("ebitda", 0)
            interest_expense = financial_data.get("interest_expense", 0)

            if interest_expense > 0:
                ratio = ebitda / interest_expense
            elif interest_expense == 0:
                ratio = float("inf") if ebitda > 0 else 0
            else:
                ratio = 0

            thresholds = self.thresholds["interest_coverage"]
            risk_level = self._assess_ratio_risk(
                ratio,
                thresholds,
                lower_is_better=False  # Higher coverage is better
            )

            interpretation = self._interpret_interest_coverage(ratio, risk_level)

            return {
                "value": round(ratio, 4) if ratio != float("inf") else None,
                "risk_level": risk_level,
                "interpretation": interpretation,
                "threshold_healthy": thresholds["healthy"],
                "threshold_warning": thresholds["warning"],
                "threshold_critical": thresholds["critical"],
                "details": {
                    "ebitda": round(ebitda, 2),
                    "interest_expense": round(interest_expense, 2),
                    "coverage_times": (
                        f"{ratio:.1f}x" if ratio != float("inf") else "No interest"
                    )
                }
            }

        except Exception as e:
            logger.error(f"Error calculating Interest Coverage: {e}")
            return self._error_result("interest_coverage", str(e))

    def _assess_ratio_risk(
        self,
        ratio: float,
        thresholds: Dict[str, float],
        lower_is_better: bool = True
    ) -> str:
        """
        Assess risk level based on ratio value and thresholds.

        Args:
            ratio: Calculated ratio value
            thresholds: Dictionary with healthy, warning, critical thresholds
            lower_is_better: If True, lower ratios are healthier

        Returns:
            Risk level string
        """
        if ratio == float("inf"):
            return "CRITICAL" if lower_is_better else "LOW"

        if lower_is_better:
            if ratio <= thresholds["healthy"]:
                return "LOW"
            elif ratio <= thresholds["warning"]:
                return "MEDIUM"
            elif ratio <= thresholds["critical"]:
                return "HIGH"
            else:
                return "CRITICAL"
        else:
            if ratio >= thresholds["healthy"]:
                return "LOW"
            elif ratio >= thresholds["warning"]:
                return "MEDIUM"
            elif ratio >= thresholds["critical"]:
                return "HIGH"
            else:
                return "CRITICAL"

    def _interpret_debt_to_equity(self, ratio: float, risk_level: str) -> str:
        """Generate interpretation for Debt-to-Equity ratio."""
        if ratio == float("inf"):
            return "Negative or zero equity - extremely high financial risk"

        if risk_level == "LOW":
            return (
                f"Conservative leverage at {ratio:.2f}x. "
                "Company maintains healthy equity cushion relative to debt."
            )
        elif risk_level == "MEDIUM":
            return (
                f"Moderate leverage at {ratio:.2f}x. "
                "Debt levels are manageable but warrant monitoring."
            )
        elif risk_level == "HIGH":
            return (
                f"High leverage at {ratio:.2f}x. "
                "Significant debt relative to equity increases financial risk."
            )
        else:
            return (
                f"Excessive leverage at {ratio:.2f}x. "
                "Company is highly leveraged with limited equity cushion."
            )

    def _interpret_debt_to_ebitda(self, ratio: float, risk_level: str) -> str:
        """Generate interpretation for Debt-to-EBITDA ratio."""
        if ratio == float("inf"):
            return "Zero or negative EBITDA - unable to service debt from operations"

        if risk_level == "LOW":
            return (
                f"Low leverage at {ratio:.1f}x EBITDA. "
                f"Could theoretically pay off all debt in {ratio:.1f} years."
            )
        elif risk_level == "MEDIUM":
            return (
                f"Moderate leverage at {ratio:.1f}x EBITDA. "
                "Debt levels require several years of earnings to repay."
            )
        elif risk_level == "HIGH":
            return (
                f"High leverage at {ratio:.1f}x EBITDA. "
                "Extended repayment timeline increases refinancing risk."
            )
        else:
            return (
                f"Excessive leverage at {ratio:.1f}x EBITDA. "
                "Debt burden significantly exceeds earnings capacity."
            )

    def _interpret_interest_coverage(self, ratio: float, risk_level: str) -> str:
        """Generate interpretation for Interest Coverage ratio."""
        if ratio == float("inf"):
            return "No interest expense or infinite coverage"

        if risk_level == "LOW":
            return (
                f"Strong interest coverage at {ratio:.1f}x. "
                "Ample earnings to cover interest obligations."
            )
        elif risk_level == "MEDIUM":
            return (
                f"Adequate interest coverage at {ratio:.1f}x. "
                "Company can meet interest payments but cushion is limited."
            )
        elif risk_level == "HIGH":
            return (
                f"Weak interest coverage at {ratio:.1f}x. "
                "Limited margin of safety for interest payments."
            )
        else:
            return (
                f"Insufficient interest coverage at {ratio:.1f}x. "
                "Company may struggle to meet interest obligations."
            )

    def _error_result(self, ratio_name: str, error_msg: str) -> Dict[str, Any]:
        """Generate error result dictionary."""
        return {
            "value": None,
            "risk_level": "ERROR",
            "interpretation": f"Error calculating {ratio_name}: {error_msg}",
            "error": error_msg
        }

    def calculate_leverage_summary(
        self,
        leverage_results: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate summary of all leverage ratios.

        Args:
            leverage_results: Dictionary containing all leverage ratio results

        Returns:
            Summary dictionary with overall assessment
        """
        # Count risk levels
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0, "ERROR": 0}

        for ratio_data in leverage_results.values():
            risk_level = ratio_data.get("risk_level", "ERROR")
            if risk_level in risk_counts:
                risk_counts[risk_level] += 1

        # Determine overall risk
        if risk_counts["CRITICAL"] > 0:
            overall_risk = "CRITICAL"
        elif risk_counts["HIGH"] > 0:
            overall_risk = "HIGH"
        elif risk_counts["MEDIUM"] > 0:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"

        return {
            "overall_risk": overall_risk,
            "risk_distribution": risk_counts,
            "ratios_analyzed": len(leverage_results),
            "key_concerns": self._identify_key_concerns(leverage_results)
        }

    def _identify_key_concerns(
        self,
        leverage_results: Dict[str, Dict[str, Any]]
    ) -> list:
        """Identify key concerns from leverage analysis."""
        concerns = []

        for ratio_name, ratio_data in leverage_results.items():
            risk_level = ratio_data.get("risk_level", "")
            if risk_level in ["HIGH", "CRITICAL"]:
                concerns.append({
                    "ratio": ratio_name,
                    "risk_level": risk_level,
                    "value": ratio_data.get("value"),
                    "interpretation": ratio_data.get("interpretation", "")
                })

        return concerns
