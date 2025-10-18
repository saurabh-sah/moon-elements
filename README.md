# moon-elements
A Python pipeline to map lunar elemental abundances from Chandrayaan-2's CLASS &amp; XSM data. It uses pyxspec for solar calibration, subtracts a modeled continuum to isolate the XRF signal, and fits peaks to measure Mg/Si &amp; Al/Si ratios. Final results are visualized on scientifically accurate HEALPix maps and interactive 3D spheres.
