#!/usr/bin/env python3

import numpy as np
import pylab as plt
import nuflux

models = [
    ("bartol",                       'C0', '-'),
    ("honda2006",                    'C0', '--'),
    ("CORSIKA_GaisserH3a_average",   'C1','-'),
    ("CORSIKA_GaisserH3a_SIBYLL-2.1",'C1','-.'),
    ("CORSIKA_GaisserH3a_QGSJET-II", 'C1','--'),
    ("IPhonda2014_spl_solmin",       'C2','-'),
    ("IPhonda2006_sno_solmin",       'C2','--'),
    ("IPhonda2014_sk_solmin",        'C2','-.'),
    ("BERSS_H3a_central",            'C3','-'),
    ("BERSS_H3p_central",            'C4','-'),
    ("BERSS_H3p_upper",              'C4','-.'),
    ("BERSS_H3p_lower",              'C4','--'),
    ("sarcevic_std",                 'C5','-'),
    ("sarcevic_max",                 'C5','-.'),
    ("sarcevic_min",                 'C5','--'),
    ("H3a_SIBYLL21",                 'C6','-'),
    ("H3a_SIBYLL23C",                'C6','--'),
]

gamma = 3
fig = plt.figure(figsize=[9.6,4.8])
ax = plt.subplot(111)

for model, color, line in models:
    flux = nuflux.makeFlux(model)
    erange = flux.energy_range

    nu_type=nuflux.NuMu
    nu_cos_zenith = 0
    nu_energy= np.logspace(np.log10(erange[0]),np.log10(erange[1]),100)
    #nu_energy= np.logspace(np.log10(erange[0]),np.log10(1000.),100)

    fluxvalues = flux.getFlux(nu_type,nu_energy,nu_cos_zenith)

    ax.plot(nu_energy, nu_energy**gamma * fluxvalues,
            label=model, color=color, ls=line)

ax.loglog()
box = ax.get_position()
ax.set_position([box.x0, box.y0+box.height*.05, box.width * 0.7, box.height *.95])
ax.set_xlabel(r"$E_\nu\ [GeV]$",fontsize=12)
ax.set_ylabel(r"$\frac{E^{3}\rm{d}\Phi}{\rm{d}\,E\rm{d}A\,\rm{d}\,\Omega\,\rm{d}t}\ \left[\frac{\rm{GeV}^{2}}{\rm{cm}^{2}\,\rm{sr}\,\rm{s}}\right]$",fontsize=18)
ax.set_title(r"$\nu_\mu\ \rm{Flux\ at\ Vertical}$")
ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

plt.show()
fig.savefig('./scripts/nuflux_models.png')
