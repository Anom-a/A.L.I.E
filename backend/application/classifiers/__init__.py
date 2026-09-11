"""Classifiers: application-level abstractions for categorising sub-questions.

This sub-package defines the :class:`SubQuestionClassifier` protocol and its
concrete implementations.  A classifier maps a domain :class:`SubQuestion` to a
:class:`ToolCategory` without performing any I/O — routing to an actual tool
happens in a separate use case.
"""
