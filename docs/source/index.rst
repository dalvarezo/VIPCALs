VIPCALs
=======

VLBI Pipeline for automated data Calibration using AIPS (in the SMILE framework)

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   overview

----

Overview
--------

**VIPCALs** is a fully automated calibration pipeline for Very Long Baseline Interferometry (VLBI) data.  
It was developed as part of the `SMILE <https://smilescience.info/>`_ (Search for Milli-Lenses) project to process thousands of datasets without human intervention.

Built on ParselTongue (`Kettenis et al. 2006 <https://www.aspbooks.org/publications/351/497.pdf>`_), a Python interface to AIPS, the pipeline offers a minimalistic graphical user interface and produces fully calibrated datasets.

Plase cite `Alvarez-Ortega et al. (2025) <https://arxiv.org/abs/2508.13282>`_ if using this code.

.. note::
   **Development status**: The pipeline is under active development. The current version supports continuum calibration of VLBA data, with support for other arrays in testing. 
   
   Bugs, feedback, and suggestions are always welcome — please contact: **dalvarez@physics.uoc.gr**

----

Acknowledgements
----------------

This work is supported by the European Research Council (ERC) under the Horizon ERC Grants 2021 programme under grant agreement No. 101040021.
