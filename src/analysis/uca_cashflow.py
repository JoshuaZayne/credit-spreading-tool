"""
UCA Cash Flow Analysis Module
=============================

Implements Uniform Credit Analysis (UCA) cash flow calculations for credit analysis.

The UCA method provides a standardized approach to analyzing a company's ability
to generate cash and service debt obligations.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class UCACashFlowAnalyzer:
    """
    Calculates cash flows using the Uniform Credit Analysis (UCA) methodology.

    The UCA format provides a standardized view of cash flow that focuses on:
    1. Cash from sales (operating activities)
    2. Cash after operations
    3. Cash available for debt service
    4. Financing surplus/deficit
    """

    def __init__(self, simulation_params: Dict[str, float] = None):
        """
        Initialize the UCA Cash Flow Analyzer.

        Args:
            simulation_params: Parameters for financial simulations
        """
        self.params = simulation_params or {}

    def analyze(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform UCA cash flow analysis on financial data.

        Args:
            financial_data: Dictionary containing financial statement data

        Returns:
            Dictionary containing UCA cash flow analysis results
        """
        try:
            # Extract required values
            net_income = financial_data.get("net_income", 0)
            depreciation = financial_data.get("depreciation_amortization", 0)
            working_capital_change = financial_data.get("working_capital_change", 0)
            capex = financial_data.get("capex", 0)
            interest_expense = financial_data.get("interest_expense", 0)
            principal_payment = financial_data.get("principal_payment", 0)
            ebitda = financial_data.get("ebitda", 0)

            # Calculate Operating Cash Flow
            # OCF = Net Income + Depreciation/Amortization - Working Capital Change
            operating_cash_flow = net_income + depreciation - working_capital_change

            # Calculate Free Cash Flow
            # FCF = Operating Cash Flow - Capital Expenditures
            free_cash_flow = operating_cash_flow - capex

            # Calculate Debt Service Requirements
            # Total Debt Service = Interest + Principal Payments
            debt_service_requirement = interest_expense + principal_payment

            # Calculate Cash Available for Debt Service
            # This is the key metric for credit analysis
            cash_available_for_debt = operating_cash_flow

            # Net Operating Income (NOI) - used for DSCR calculation
            # NOI is typically EBITDA for commercial lending
            noi = ebitda

            # Additional UCA metrics
            cash_after_debt_service = cash_available_for_debt - debt_service_requirement

            # UCA Coverage Ratio
            uca_coverage = (
                cash_available_for_debt / debt_service_requirement
                if debt_service_requirement > 0
                else float("inf")
            )

            # Build detailed breakdown
            details = {
                "components": {
                    "net_income": net_income,
                    "add_back_depreciation": depreciation,
                    "less_working_capital_increase": working_capital_change,
                    "operating_cash_flow": operating_cash_flow,
                    "less_capex": capex,
                    "free_cash_flow": free_cash_flow
                },
                "debt_service": {
                    "interest_expense": interest_expense,
                    "principal_payment": principal_payment,
                    "total_debt_service": debt_service_requirement
                },
                "coverage": {
                    "uca_coverage_ratio": round(uca_coverage, 4) if uca_coverage != float("inf") else None,
                    "cash_after_debt_service": cash_after_debt_service
                }
            }

            result = {
                "operating_cash_flow": round(operating_cash_flow, 2),
                "free_cash_flow": round(free_cash_flow, 2),
                "debt_service_requirement": round(debt_service_requirement, 2),
                "cash_available_for_debt": round(cash_available_for_debt, 2),
                "noi": round(noi, 2),
                "uca_coverage_ratio": round(uca_coverage, 4) if uca_coverage != float("inf") else None,
                "cash_after_debt_service": round(cash_after_debt_service, 2),
                "details": details
            }

            logger.debug(f"UCA Analysis complete: OCF=${operating_cash_flow:,.2f}, FCF=${free_cash_flow:,.2f}")

            return result

        except Exception as e:
            logger.error(f"Error in UCA cash flow analysis: {e}")
            return {
                "operating_cash_flow": None,
                "free_cash_flow": None,
                "debt_service_requirement": None,
                "cash_available_for_debt": None,
                "noi": None,
                "error": str(e)
            }

    def calculate_sources_and_uses(self, financial_data: Dict) -> Dict[str, Any]:
        """
        Calculate detailed sources and uses of cash.

        Args:
            financial_data: Dictionary containing financial statement data

        Returns:
            Dictionary showing sources and uses of cash
        """
        # Sources of cash
        sources = {
            "net_income": financial_data.get("net_income", 0),
            "depreciation": financial_data.get("depreciation_amortization", 0),
            "decrease_in_working_capital": max(0, -financial_data.get("working_capital_change", 0))
        }
        total_sources = sum(sources.values())

        # Uses of cash
        uses = {
            "capital_expenditures": financial_data.get("capex", 0),
            "debt_principal_payment": financial_data.get("principal_payment", 0),
            "increase_in_working_capital": max(0, financial_data.get("working_capital_change", 0))
        }
        total_uses = sum(uses.values())

        return {
            "sources": sources,
            "total_sources": round(total_sources, 2),
            "uses": uses,
            "total_uses": round(total_uses, 2),
            "net_cash_flow": round(total_sources - total_uses, 2)
        }

    def assess_cash_flow_quality(self, uca_result: Dict) -> Dict[str, Any]:
        """
        Assess the quality of cash flows for credit purposes.

        Args:
            uca_result: Results from UCA analysis

        Returns:
            Quality assessment of cash flows
        """
        ocf = uca_result.get("operating_cash_flow", 0) or 0
        fcf = uca_result.get("free_cash_flow", 0) or 0
        coverage = uca_result.get("uca_coverage_ratio")

        # Assess OCF quality
        if ocf > 0:
            ocf_quality = "POSITIVE"
            ocf_assessment = "Company generates positive operating cash flow"
        else:
            ocf_quality = "NEGATIVE"
            ocf_assessment = "Company has negative operating cash flow - requires external financing"

        # Assess FCF quality
        if fcf > 0:
            fcf_quality = "POSITIVE"
            fcf_assessment = "Company generates free cash flow after capital expenditures"
        else:
            fcf_quality = "NEGATIVE"
            fcf_assessment = "Capital expenditures exceed operating cash flow"

        # Assess coverage quality
        if coverage is None:
            coverage_quality = "N/A"
            coverage_assessment = "No debt service requirement"
        elif coverage >= 1.5:
            coverage_quality = "STRONG"
            coverage_assessment = "Strong coverage of debt service requirements"
        elif coverage >= 1.25:
            coverage_quality = "ADEQUATE"
            coverage_assessment = "Adequate coverage with limited cushion"
        elif coverage >= 1.0:
            coverage_quality = "MARGINAL"
            coverage_assessment = "Marginal coverage - potential stress in downturn"
        else:
            coverage_quality = "INSUFFICIENT"
            coverage_assessment = "Insufficient cash flow to cover debt service"

        return {
            "operating_cash_flow": {
                "quality": ocf_quality,
                "assessment": ocf_assessment
            },
            "free_cash_flow": {
                "quality": fcf_quality,
                "assessment": fcf_assessment
            },
            "debt_service_coverage": {
                "quality": coverage_quality,
                "assessment": coverage_assessment
            },
            "overall_quality": self._determine_overall_quality(
                ocf_quality, fcf_quality, coverage_quality
            )
        }

    def _determine_overall_quality(
        self,
        ocf_quality: str,
        fcf_quality: str,
        coverage_quality: str
    ) -> str:
        """Determine overall cash flow quality rating."""
        if ocf_quality == "NEGATIVE":
            return "POOR"
        if coverage_quality in ["INSUFFICIENT", "MARGINAL"]:
            return "WEAK"
        if fcf_quality == "NEGATIVE":
            return "FAIR"
        if coverage_quality == "STRONG" and fcf_quality == "POSITIVE":
            return "STRONG"
        return "ADEQUATE"
