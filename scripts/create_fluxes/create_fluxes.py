#!/usr/bin/python3

################################################################################
## This script generates new atmospheric fluxes for the nuflux project.
##
## It can:
##   - Create 2D tabulated flux data using MCEq
##   - Spline the tabulated data using photospline to create FITS files
##   - Read the FITS files
##   - Plot the data and splines
## You can use it to do all, any or just one of the above, by selecting
## functions at the very end of the file.
## To get an idea of the flux interpolation process, you can run it
## with the provided "exampleflux" data (that resembles an MCEq-created
## data file).
##
## Created for the nuflux project as part of an IceCube service task.
## Created by: Raffaela Busse (WWU Münster), rbusse@icecube.wisc.edu
################################################################################


import os
from shutil import copyfile
import math
import numpy as np

###--- Global settings ---------------------------------------------------------
# Please provide a name for your new fluxes, and define the path to the
# working directory. All necessary folders are being set up for you automatically.
working_path = './'
name     = 'H3a_SIBYLL23C'
# name     = 'exampleflux'
dirname  = name
os.chdir(working_path)
if not os.path.exists(dirname):
    os.mkdir(dirname)
    os.mkdir(dirname + '/data')         # The 2D tabulated data files. If MCEq is used, this is where it puts the solutions.
    os.mkdir(dirname + '/splines')      # The photospline generated FITS files are stored here.
    os.mkdir(dirname + '/plotdata')     # Data for plots (re-scaled and coverted to physical units for easy plotting) goes here.
    os.mkdir(dirname + '/plots')        # Plots are being saved in here.

# Particle types you want to make fluxes for (choose from the list by commenting
# out particles you don't want, or by list comprehension, or add your own):
particles = [
    # particle name     LaTeX code (for plots)            line style (for plots)
    ### Total total flux:
    ('total_nue',      r'total $\nu_{e}$',                       'solid'),
    ('total_nuebar',   r'total $\bar{\nu}_{e}$',                 'solid'),
    ('total_numu',     r'total $\nu_{\mu}$',                     'solid'),
    ('total_numubar',  r'total $\bar{\nu}_{\mu}$',               'solid'),
    ('total_nutau',     r'total $\nu_{\tau}$',                   'solid'),
    ('total_nutaubar',  r'total $\bar{\nu}_{\tau}$',             'solid'),   # 5
    ### Total conventional flux:
    ('conv_nue',       r'conv. $\nu_{e}$',                       '--'),
    ('conv_nuebar',    r'conv. $\bar{\nu}_{e}$',                 '--'),
    ('conv_numu',      r'conv. $\nu_{\mu}$',                     '--'),
    ('conv_numubar',   r'conv. $\bar{\nu}_{\mu}$',               '--'),      # 9
    ### Conventional flux from pions/kaons:
    ('pi_nue',         r'(from $\pi$) $\nu_{e}$',                   ':'),
    ('k_nue',          r'(from $K^{\pm}$) $\nu_{e}$',                     ':'),
    ('K0_nue',         r'(from $K^{0}$) $\nu_{e}$',                 '-.'),
    ('pi_nuebar',      r'(from $\pi$) $\bar{\nu}_{e}$',             ':'),
    ('k_nuebar',       r'(from $K^{\pm}$) $\bar{\nu}_{e}$',               ':'),
    ('K0_nuebar',      r'(from $K^{0}$) $\bar{\nu}_{e}$',           '-.'),
    ('pi_numu',        r'(from $\pi$) $\nu_{\mu}$',                 ':'),
    ('k_numu',         r'(from $K^{\pm}$) $\nu_{\mu}$',                   ':'),
    ('K0_numu',        r'(from $K^{0}$) $\nu_{\mu}$',               '-.'),
    ('pi_numubar',     r'(from $\pi$) $\bar{\nu}_{\mu}$',           ':'),
    ('k_numubar',      r'(from $K^{\pm}$) $\bar{\nu}_{\mu}$',             ':'),
    ('K0_numubar',     r'(from $K^{0}$) $\bar{\nu}_{\mu}$',         '-.'),  # 21
    ### From muons:
    ('mu_nue',           r'(from $\mu$) $\nu_{e}$',                  '-'),
    ('mu_nuebar',        r'(from $\mu$) $\bar{\nu}_{e}$',            '-'),
    ('mu_numu',          r'(from $\mu$) $\nu_{\mu}$',                '-'),
    ('mu_numubar',       r'(from $\mu$) $\bar{\nu}_{\mu}$',          '-'),  # 26
    ### Conventional flux from all other:
    ### (According to the plots, these seem to be equal to the total fluxes
    ### for some reason)
    # ('nue',            r'conv. (other srcs) $\nu_{e}$',          '-.'),
    # ('nuebar',         r'conv. (other srcs) $\bar{\nu}_{e}$',    '-.'),
    # ('numu',           r'conv. (other srcs) $\nu_{\mu}$',        '-.'),
    # ('numubar',        r'conv. (other srcs) $\bar{\nu}_{\mu}$',  '-.'),
    # ('nutau',          r'conv. (other srcs) $\nu_{\tau}$',       '-.'),
    # ('nutaubar',       r'conv. (other srcs) $\bar{\nu}_{\tau}$', '-.'),
    ### Total prompt flux:
    ('prompt_nue',         r'prompt $\nu_{e}$',                      '--'),
    ('prompt_nuebar',      r'prompt $\bar{\nu}_{e}$',                '--'),
    ('prompt_numu',        r'prompt $\nu_{\mu}$',                    '--'),
    ('prompt_numubar',     r'prompt $\bar{\nu}_{\mu}$',              '--'),
    ('prompt_nutau',       r'prompt $\nu_{\tau}$',                   '--'),
    ('prompt_nutaubar',    r'prompt $\bar{\nu}_{\tau}$',             '--'), # 32
]
# particles = particles[0:1]
# particles = particles[0:4]
# particles = particles[:18] + particles[24:]

# The following is a setting necessary for MCEq. Even if we don't use MCEq, it's
# important for the file handling of the other routines that we set this globally.
# Leave at mag = 0 if unsure. More information in the solve_mceqs() routine.
mag = 0

###-----------------------------------------------------------------------------

def Solve_mceqs(particle):
    ### Create 2D tabulated spectra with MCEq
    import crflux.models as crf
    from MCEq.core import config, MCEqRun

    def Convert_name(particle):
        # MCEq can't handle "bar"s in particle names. It wants "anti"s instead.
        if 'bar' in particle[0]:
            pname = (particle[0].replace('_', '_anti') if '_' in particle[0] else 'anti' + particle[0])
            pname = pname.replace('bar', '')
        else:
            pname = particle[0]
        return pname

    # Cosmic ray flux at the top of the atmosphere:
    primary_model = (crf.HillasGaisser2012, 'H3a')
    # High-energy hadronic interaction model:
    interaction_model = 'SIBYLL21'
    # Zenith angles:
    zenith_deg = np.append(np.arange(0., 90., 10), 89)
    # By setting mag != 0, the fluxes are multiplied by that factor of E [GeV]
    # in MCEq to stress steaper parts of the spectrum:
    # mag = mag

    headr = (
    savename.replace('_', '\t') + '\n'
    'energy [GeV]\t' + ' '.join([str(z) + ' deg\t' for z in zenith_deg])
    )

    ## Solve the equation system
    solutions = []
    for angle in zenith_deg:
        print(
            '\n=== Solving MCEq for ' + particle[0] + ' '
            + primary_model[1] + ' ' + interaction_model
            + ' mag=' + str(mag) + ' ' + str(angle) + ' deg'
        )
        mceq = MCEqRun(interaction_model, primary_model, angle)
        mceq.solve()
        energy = mceq.e_grid
        solutions.append(mceq.get_solution(Convert_name(particle), mag))

    solutions.insert(0, energy)
    solutions = np.array(solutions)
    np.savetxt(
        dirname + '/data/' + savename + '.dat', np.transpose(solutions),
        fmt='%.8e', header=headr, delimiter='\t'
    )


def Spline_fluxes(particle):
    ### Spline the solutions with photospline.
    from photospline import glam_fit, ndsparse, bspline

    def Read_data():
        ### Read data from data file/ MCEq solution file. If your data is from
        ### other sources rather than created by the Solve_mceqs() routine of
        ### this script, make sure it has the same format as the data in the
        ### example data file "example_data.dat".

        filename = dirname + '/data/' + savename + '.dat'
        # Read header of data file:
        with open(filename) as f:
            f.readline()
            angles = f.readline().split()[3:]
        # Check whether we have zenith or cos(zenith) angles:
        # (THE FOLLOWING ONLY WORKS IF THE DATA FORMAT IS STRICTLY FOLLOWED.
        # Please double check whether you get the correct data in the correct
        # order out of your files. If this causes you headaches, you could
        # just define your cos(zenith) range by hand below.)
        if 'deg' in angles[1]:
            angles = angles[::2]
            angles = np.array([float(value) for value in angles])
            coszen = np.cos(np.radians(angles))
        else:
            coszen = np.array([float(value) for value in angles])
        # Or define cos(zenith) range by hand:
        # coszen = np.array([0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])


        # Read data of data file:
        data = np.loadtxt(filename, unpack=True)
        energy, data = data[0], data[1:]
        # Check whether the data is stored in reverse order (1 > cos(zenith) > 0).
        # This is necessary because a reverted order would mess up the splining
        # process later.
        if coszen[0]>coszen[1]:
            # We want 0 < cos(zenith) < 1. So we revert the order of the two
            # arrays, so that the first dataset matches cos(zenith)=0=90deg and
            # the last matches cos(zenith)=1=0deg:
            coszen = coszen[::-1]
            data = data[::-1]
        else:
            # If not, we keep everything as it is:
            coszen = coszen
            data = data
        # Now we transpose the data so we have an angular spectrum for each energy
        # instead of an energy spectrum for each zenith angle. That's how nuflux wants it!
        data = np.transpose(data)
        # Energy bins and flux values are stored as base-10 log in nuflux, so we are
        # converting them here. In the fluxes, there may be occurences of negative
        # values or zeros which are considered unphysical and therefore set to NaN
        # (otherwise they will later mess up the fitting process).
        energy = np.log10(energy)
        data = [np.where(flux<=0, np.nan, flux) for flux in data]
        data = np.log10(data)
        # In the last step we prune all arrays that contain NaN values:
        allnans = np.where(np.isnan([np.sum(flux) for flux in data]))[0]
        energy = np.delete(energy, allnans)
        data = np.delete(data, allnans, 0)
        # print(data)
        # print(len(energy), len(data))
        centers = [energy, coszen]
        return centers, data

    def Create_knots(arr, order):
        # print(arr)
        knots = np.linspace(arr[0], arr[-1], len(arr)+1)
        # Pad knots out for full support at the boundaries (taken from
        # test_fit.py in photospline module):
        pre = knots[0] - (knots[1]-knots[0])*np.arange(order, 0, -1)
        post = knots[-1] + (knots[-1]-knots[-2])*np.arange(1, order+1)
        return np.concatenate((pre, knots, post))

    def Check_spline(arr):
        # Checking integrity of spline (i.e., how many elements of y are all-zero
        # or all nan?) for debugging purposes.
        zeros, nans = [], []
        zeros.append([i for i in y if sum(i) == 0])
        zeros.append([i for i in np.transpose(y) if sum(i) == 0])
        nans.append([i for i in y if math.isnan(sum(i))])
        nans.append([i for i in np.transpose(y) if math.isnan(sum(i))])
        print('\nChecking integrity of spline surface:')
        print('all-zero\ty ' + str(len(zeros[0])) + '\tyT ' + str(len(zeros[1])))
        print('all-nan\t\ty ' + str(len(nans[0])) + '\tyT ' + str(len(nans[1])))
        if (len(zeros[0]) + len(zeros[1]) > 20) or (len(nans[0]) + len(nans[1]) > 20):
            print('=== WARNING: Spline might be corrupt!')

    def Save_data_for_plots(centers, data, xfine, y):
        ### In former versions of this script, the data was plotted on the fly. I've
        ### decided to save the plot data in a separate file, so that it can be
        ### loaded without kicking off a splining process every time.

        # Convert data and splines from base log 10:
        energypow = np.power(10, centers[0])
        datapow   = np.power(10, data)
        xfinepow  = np.power(10, xfine)
        ypow      = np.power(10, y)
        # For each energy, we append a 10-item coszen data and -spline array in
        # interlocking order:
        savedata = []
        for e, entry in enumerate(energypow):
            savedata.append(list(sum(list(zip(datapow[e], ypow[e])), ())))
            savedata[e].insert(0, entry)

        header = (
            savename.replace('_', '\t') + '\n'
            'coszen\t' + ' '.join(['%.2f\t' % z for z in centers[1]]) + '\n'
            'E [GeV]\t' + ' '.join(['(%.2f data, spline)\t' % z for z in centers[1]])
        )
        np.savetxt(
            dirname + '/plotdata/' + savename + '_plotdata.dat', savedata,
            fmt='%.4e', header=header
        )

    # Load data from file:
    centers, data = Read_data()

    #--- Set the splining parameters -------------------------------------------
    w = 1.
    order = [2, 3]
    penalty_order = order
    knots = [Create_knots(centers[0], order[0]), Create_knots(centers[1], order[1])]
    smooth = [1e-9, 1]
    # smooth = [1e-2, 1]
    # Define a fine-grid area to later evaluate the spline over (or simply
    # choose the centers again). This has no influence on the saved FITS file:
    xfine = centers
    # xfine = [np.linspace(energy[0], energy[-1], 500),
    #          np.linspace(coszen[0], coszen[-1], 100)]

    # print(xfine)
    # print(knots)

    datasp, w = ndsparse.from_data(data, data+w)
    spline = glam_fit(datasp, w, centers, knots, order, smooth, penalty_order)
    y = spline.grideval(xfine)
    Save_data_for_plots(centers, data, xfine, y)
    spline.write(dirname + '/splines/' + savename + '.fits')
    # Uncomment for debugging:
    # Check_spline(y)


def Plot_splines():
    ### Plot'em!
    import seaborn as sb
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.backends.backend_pdf import PdfPages as pdf

    def Load_data(savename):
        ### Loading the plot data previously stored by Save_data_for_plots():

        filename = dirname + '/plotdata/' + savename + '_plotdata.dat'
        # Load coszen axis:
        with open(filename) as f:
            xc = [line for line in f if line.startswith('# coszen')]
        xc = [float(i) for i in xc[0].split()[2:]]
        # Load energy axis, datapoints and splines:
        loaddata = np.loadtxt(filename, unpack=True)
        xe = loaddata[0]
        datapoints   = loaddata[1::2]
        splines      = loaddata[2::2]
        return(xe, xc, datapoints, splines)

    def Create_title(particle, flavor):
        ### Create plot title.
        title = (
            'atmospheric ' + particle[1] + ' flux '
            'for ' + name + ', tabulated data and spline fits'
        )
        title_flavor = (
            'atmospheric ' + flavor[1] + ' fluxes '
            'for ' + name + ', tabulated data and spline fits'
        )
        return title, title_flavor

    def Create_axlabels():
        ### Create title and axis labels.
        xlabel = r'kinetic energy $E$ [GeV]'
        # The unit of the flux is 1/(GeV s cm^2 sr). However keep in mind to account
        # for the magnification factor (mag) which may introduce several more GeV's.
        if mag == 0:
            ylabel = r'flux $\Phi$ [GeV$^{-1}$cm$^{-2}$s$^{-1}$sr$^{-1}$]'
        elif mag == 1:
            ylabel = r'flux $\Phi$ [GeV$^{-1}$cm$^{-2}$s$^{-1}$sr$^{-1}$] $\times$ E [GeV]'
        else:
            ylabel = (
                  r'flux $\Phi$ [GeV$^{-1}$cm$^{-2}$s$^{-1}$sr$^{-1}$]'
                + r' $\times$ E$^{' + str(mag) + r'}$'
                + r' [GeV$^{' + str(mag) + r'}$] '
            )
        return xlabel, ylabel

    def Create_label(particle):
        label = (
            particle[1].split(')')[0].replace('(', '') if 'from' in particle[1]
            else particle[1].split(' ')[0]
        )
        return label

    sb.set_context(context='notebook', font_scale=1.2, rc={"lines.linewidth": 2.0})
    sb.set_style('whitegrid')
    xlabel, ylabel = Create_axlabels()
    custom_legend = [Line2D([0], [0], color='gray', lw=0, marker='+',
                            label=r'data for $\cos(\theta)=1$')]
    short_legend = [Line2D([0], [0], color='gray', lw=0, marker='+', label=r'data')]
    numcols = 3

    flavors = [
        ('nue',      r'$\nu_{e}$'),
        ('nuebar',   r'$\bar{\nu}_{e}$'),
        ('numu',     r'$\nu_{\mu}$'),
        ('numubar',  r'$\bar{\nu}_{\mu}$'),
        ('nutau',    r'$\nu_{\tau}$'),
        ('nutaubar', r'$\bar{\nu}_{\tau}$')
    ]
    flavor_colors  = plt.cm.jet(np.linspace(0,1,7))

    for f, flavor in enumerate(flavors):
        pdf_flavor = pdf(dirname + '/plots/perflavor_mag' + str(mag) + '_' + flavor[0] + '.pdf')
        fig3, ax3   = plt.subplots(1, 1, figsize=(9,5))
        fig3.subplots_adjust(bottom=0.14, top=0.91, left=0.12, right=0.95, wspace=0.2)
        fig4, axes4 = plt.subplots(3, numcols, figsize=(9,5), sharex='col')
        # fig4, axes4 = plt.subplots(3, 2, figsize=(9,5), sharex='col')
        fig4.subplots_adjust(bottom=0.13, top=0.81, left=0.1, right=0.95, wspace=0.2, hspace=0.3)
        fig4.text(0.5, 0.03, r'cosine of zenith angle $\cos(\theta)$', ha='center')
        fig4.text(0.02, 0.5, ylabel, va='center', rotation='vertical')
        # ax3.text(0.15, 0.1, r'data for $\cos(\theta)=1$', horizontalalignment='center',
        #     verticalalignment='center', transform = ax3.transAxes)

        p=0
        for particle in particles:
            if (
                (('bar' not in flavor[0]) and (flavor[0] in particle[0]) and ('bar' not in particle[0]))
                or (('bar' in flavor[0]) and (flavor[0] in particle[0]))
            ):
                savename = name + '_' + particle[0]
                xe, xc, datapoints, splines = Load_data(savename)
                # Transpose the data for energy dependence plots:
                datapointsT, splinesT = np.transpose(datapoints), np.transpose(splines)
                # Set iterators for xe and coszen dependence plotting (because we don't
                # want hundreds of fluxes in a plot):
                eit, cit = int(len(splinesT)/9), int(len(datapoints)/9)
                colors  = plt.cm.jet(np.linspace(0,1,len(splines[::cit])))
                title, title_flavor = Create_title(particle, flavor)

                fig1, ax1 = plt.subplots(1, 1, figsize = (9, 5))
                fig1.subplots_adjust(bottom=0.14, top=0.91, left=0.12, right=0.95, wspace=0.2)
                fig2, axes2 = plt.subplots(3, numcols, figsize=(9, 5), sharex='col')
                # fig2, axes2 = plt.subplots(3, 2, figsize=(9, 5), sharex='col')
                fig2.subplots_adjust(bottom=0.13, top=0.87, left=0.1, right=0.95, wspace=0.2, hspace=0.3)
                fig2.suptitle(title, fontsize=14)
                fig2.text(0.5, 0.03, r'cosine of zenith angle $\cos(\theta)$', ha='center')
                fig2.text(0.02, 0.5, ylabel, va='center', rotation='vertical')
                fig4.suptitle(title_flavor, fontsize=14)


                ##--- Energy dependence plots ----------------------------------
                pdf_particle = pdf(dirname + '/plots/' + savename + '.pdf')

                # Plot the splines:
                for spline, label, color in zip(splines[::cit], xc[::cit], colors):
                    ax1.loglog(xe, spline, label='%.2f' % label, color=color)
                # Plot the data points:
                ax1.loglog(xe, datapoints[-1], lw=0, marker='+', color='gray', alpha=0.4)
                ax1.set_title(title)
                ax1.set_xlabel(xlabel)
                ax1.set_ylabel(ylabel)
                leg11 = ax1.legend(handles=custom_legend, loc='upper right')
                leg12 = ax1.legend(title=r'$\cos(\theta)$', loc='lower left')
                ax1.add_artist(leg11)

                ax3.loglog(xe, datapoints[-1], lw=0, marker='+', color='gray', alpha=0.4)
                ax3.loglog(xe, splines[-1], label=Create_label(particle), ls=particle[2],
                           color=flavor_colors[p], alpha=0.8)
                # if 'pi' in particle[0]:
                #     pi_values = splines[-1]
                # if 'k' in particle[0]:
                #     ax3.loglog(xe[:110], pi_values[:110] + splines[-1][:110], label='sum', ls='--', color='black')
                ax3.set_title(title_flavor)
                ax3.set_xlabel(xlabel)
                ax3.set_ylabel(ylabel)
                leg31 = ax3.legend(handles=custom_legend, loc='upper right')
                leg32 = ax3.legend(loc='lower left')
                ax3.add_artist(leg31)

                ##--- Coszen dependence plots ----------------------------------
                # Plot the data points and splines:
                for ax2, ax4, dataset, spline, label, color in zip(
                    axes2.flatten(),
                    axes4.flatten(),
                    # datapointsT[::eit],
                    # splinesT[::eit],
                    # xe[::eit],
                    datapointsT[21::10],
                    splinesT[21::10],
                    xe[21::10],
                    # datapointsT[0::20],
                    # splinesT[0::20],
                    # xe[0::20],
                    colors
                ):
                    ax2.tick_params(axis='both', which='major', labelsize=10)
                    ax2.yaxis.offsetText.set_fontsize(10)
                    ax2.set_title(r'at $E\approx$%.0e' % label + ' GeV', fontsize=12, loc='right')
                    ax2.plot(xc, dataset, lw=0, marker='+', color='gray', alpha=0.4)
                    ax2.plot(xc, spline, color=color)
                    ax2.ticklabel_format(axis='y', style='sci', scilimits=(0,0))

                    ax4.tick_params(axis='both', which='major', labelsize=10)
                    ax4.yaxis.offsetText.set_fontsize(10)
                    ax4.set_title(r'at $E\approx$%.0e' % label + ' GeV', fontsize=12, loc='right')
                    ax4.plot(xc, dataset, lw=0, marker='+', color='gray', alpha=0.4)
                    ax4.plot(xc, spline, color=flavor_colors[p], alpha=0.9,
                             ls=particle[2], label=Create_label(particle))
                    ax4.ticklabel_format(axis='y', style='sci', scilimits=(0,0))
                    handles, labels = ax4.get_legend_handles_labels()

                p+=1

                pdf_particle.savefig(fig1)
                pdf_particle.savefig(fig2)
                pdf_particle.close()
        if p:
            leg41 = fig4.legend(handles=short_legend, loc='upper left', fontsize=12,
                                bbox_to_anchor=(0.05, 0.45, 0.86, 0.5))
            leg42 = fig4.legend(handles, labels, loc='upper left', ncol=7,
                                mode='expand', bbox_to_anchor=(0.16, 0.45, 0.80, 0.5),
                                fontsize=12)
        pdf_flavor.savefig(fig3)
        pdf_flavor.savefig(fig4)
        pdf_flavor.close()


def Read_fits(filename):
    ### This function reads FITS files for debugging purposes.
    from astropy.io import fits


    print('=== FITS file header information:')
    # if 'anti' in filename:
    #     filename = filename.replace('anti', '').replace('.fits', 'bar.fits')
    image = fits.open(filename)
    ## Header information:
    image.info()
    hdr = image[0].header
    # print(repr(hdr))
    ## Stored data:
    # print(image[0].data)
    # print(image[1].data)
    # print(image[2].data)
    print(image[3].data)
    print(np.power(10, image[3].data))
    # print(np.log10(image[3].data))
    image.close()


#--- make it so! ---------------------------------------------------------------

for particle in particles:
    # print('\n' + particle[0])
    savename = name + '_' + particle[0] + ('_mag' + str(mag) if mag != 0 else '')
    # savename = name + '_' + particle[0] + '_mag' + str(mag)
    ##--- Execute once and then uncomment, afterwards load data from files to
    ##--- considerably reduce computing time. If you are using the example data,
    ##--- you can skip this step, too:
    # Solve_mceqs(particle)
    ##--- Spline the fluxes with photospline, and save data in plottable format:
    # Spline_fluxes(particle)
    ##--- Read the fits to verify they're in the correct format:
    # Read_fits(dirname + '/splines/' + savename + '.fits')

##--- Plot stuff (for all selected particles at once)
Plot_splines()
