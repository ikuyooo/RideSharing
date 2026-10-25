"""Business modules of the modular monolith (Revision 9, Section 54).

Each package owns the tables declared in its `models.py`. Other modules must
not import another module's `models` to query it; they call its `service`.
"""
