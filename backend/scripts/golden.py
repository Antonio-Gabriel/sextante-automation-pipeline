"""Golden set measurement (NFR-TST-001, D-3.18). Run with ``make golden``.

Measures extraction, entity, target sheet, line types and refusals on the sample
invoices, without calling the model. Needs SEXTANTE_GOLDEN_SAMPLES_DIR and the target
entity variables of config/.env. Item codes are measured with the real model by a
separate manual command, which arrives with the Claude adapter (ticket 11).
"""

import os
import sys

from sextante.golden_set import golden_main

if __name__ == "__main__":
    sys.exit(golden_main(os.environ, print))
