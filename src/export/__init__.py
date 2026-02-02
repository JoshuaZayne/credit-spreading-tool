"""
Export module for Credit Spreading Tool.

This module handles exporting analysis results to various formats,
primarily Excel workbooks with professional formatting.
"""

from .excel_exporter import ExcelExporter

__all__ = ["ExcelExporter"]
