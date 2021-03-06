#!/usr/bin/env python2
"""
convert output of gamess/GAU$$IAN to ezfio

Usage:
    qp_convert_output_to_ezfio.py <file.out> [-o <ezfio_directory>]

Option:
    file.out is the file to check (like gamess.out)
    folder.ezfio is the name you whant for the ezfio
        (by default is file.out.ezfio)

"""

import sys
import os
from functools import reduce

# ~#~#~#~#~#~#~#~ #
# Add to the path #
# ~#~#~#~#~#~#~#~ #


try:
    QP_ROOT = os.environ["QP_ROOT"]
except:
    print "Error: QP_ROOT environment variable not found."
    sys.exit(1)
else:
    sys.path = [ QP_ROOT + "/install/EZFIO/Python", 
                 QP_ROOT + "/install/resultsFile", 
                 QP_ROOT + "/install", 
                 QP_ROOT + "/scripts"] + sys.path

# ~#~#~#~#~#~ #
# I m p o r t #
# ~#~#~#~#~#~ #

from ezfio import ezfio

try:
    from resultsFile import *
except:
    print "Error: resultsFile Python library not installed"
    sys.exit(1)

from docopt import docopt

#  _
# |_    ._   _ _|_ o  _  ._
# | |_| | | (_  |_ | (_) | |
#


def write_ezfio(res, filename):

    res.clean_uncontractions()
    ezfio.set_file(filename)

    #  _
    # |_ |  _   _ _|_ ._ _  ._   _
    # |_ | (/_ (_  |_ | (_) | | _>
    #
    ezfio.set_electrons_elec_alpha_num(res.num_alpha)
    ezfio.set_electrons_elec_beta_num(res.num_beta)

    #
    # |\ |      _ |  _  o
    # | \| |_| (_ | (/_ |
    #

    # ~#~#~#~ #
    # I n i t #
    # ~#~#~#~ #

    charge = []
    coord_x = []
    coord_y = []
    coord_z = []

    # ~#~#~#~#~#~#~ #
    # P a r s i n g #
    # ~#~#~#~#~#~#~ #

    for a in res.geometry:
        charge.append(a.charge)
        if res.units == 'BOHR':
            coord_x.append(a.coord[0])
            coord_y.append(a.coord[1])
            coord_z.append(a.coord[2])
        else:
            coord_x.append(a.coord[0] / a0)
            coord_y.append(a.coord[1] / a0)
            coord_z.append(a.coord[2] / a0)


    # ~#~#~#~#~ #
    # W r i t e #
    # ~#~#~#~#~ #

    ezfio.set_nuclei_nucl_num(len(res.geometry))
    ezfio.set_nuclei_nucl_charge(charge)

    # Transformt H1 into H
    import re
    p = re.compile(ur'(\d*)$')
    label = [p.sub("", x.name).capitalize() for x in res.geometry]
    ezfio.set_nuclei_nucl_label(label)

    ezfio.set_nuclei_nucl_coord(coord_x + coord_y + coord_z)

    #                 _
    #   /\   _   _   |_)  _.  _ o  _
    #  /--\ (_) _>   |_) (_| _> | _>
    #

    # ~#~#~#~ #
    # I n i t #
    # ~#~#~#~ #

    import string
    at = []
    num_prim = []
    power_x = []
    power_y = []
    power_z = []
    coefficient = []
    exponent = []

    res.convert_to_cartesian()
    # ~#~#~#~#~#~#~ #
    # P a r s i n g #
    # ~#~#~#~#~#~#~ #

    for b in res.basis:
        c = b.center
        for i, atom in enumerate(res.geometry):
            if atom.coord == c:
                at.append(i + 1)
        num_prim.append(len(b.prim))
        s = b.sym
        power_x.append(string.count(s, "x"))
        power_y.append(string.count(s, "y"))
        power_z.append(string.count(s, "z"))
        coefficient.append(b.coef)
        exponent.append([p.expo for p in b.prim])

    # ~#~#~#~#~ #
    # W r i t e #
    # ~#~#~#~#~ #

    ezfio.set_ao_basis_ao_num(len(res.basis))
    ezfio.set_ao_basis_ao_nucl(at)
    ezfio.set_ao_basis_ao_prim_num(num_prim)
    ezfio.set_ao_basis_ao_power(power_x + power_y + power_z)

    # ~#~#~#~#~#~#~ #
    # P a r s i n g #
    # ~#~#~#~#~#~#~ #

    prim_num_max = ezfio.get_ao_basis_ao_prim_num_max()

    for i in range(len(res.basis)):
        coefficient[
            i] += [0. for j in range(len(coefficient[i]), prim_num_max)]
        exponent[i] += [0. for j in range(len(exponent[i]), prim_num_max)]

    coefficient = reduce(lambda x, y: x + y, coefficient, [])
    exponent = reduce(lambda x, y: x + y, exponent, [])

    coef = []
    expo = []
    for i in range(prim_num_max):
        for j in range(i, len(coefficient), prim_num_max):
            coef.append(coefficient[j])
            expo.append(exponent[j])

    # ~#~#~#~#~ #
    # W r i t e #
    # ~#~#~#~#~ #

    ezfio.set_ao_basis_ao_coef(coef)
    ezfio.set_ao_basis_ao_expo(expo)
    ezfio.set_ao_basis_ao_basis("Read by resultsFile")

    #                _
    # |\/|  _   _   |_)  _.  _ o  _
    # |  | (_) _>   |_) (_| _> | _>
    #

    # ~#~#~#~ #
    # I n i t #
    # ~#~#~#~ #

    MoTag = res.determinants_mo_type
    ezfio.set_mo_basis_mo_label('Orthonormalized')
    MO_type = MoTag
    allMOs = res.mo_sets[MO_type]

    # ~#~#~#~#~#~#~ #
    # P a r s i n g #
    # ~#~#~#~#~#~#~ #

    try:
        closed = [(allMOs[i].eigenvalue, i) for i in res.closed_mos]
        active = [(allMOs[i].eigenvalue, i) for i in res.active_mos]
        virtual = [(allMOs[i].eigenvalue, i) for i in res.virtual_mos]
    except:
        closed = []
        virtual = []
        active = [(allMOs[i].eigenvalue, i) for i in range(len(allMOs))]

    closed = map(lambda x: x[1], closed)
    active = map(lambda x: x[1], active)
    virtual = map(lambda x: x[1], virtual)
    MOindices = closed + active + virtual

    MOs = []
    for i in MOindices:
        MOs.append(allMOs[i])

    mo_tot_num = len(MOs)
    while len(MOindices) < mo_tot_num:
        MOindices.append(len(MOindices))

    MOmap = list(MOindices)
    for i in range(len(MOindices)):
        MOmap[i] = MOindices.index(i)

    energies = []
    for i in xrange(mo_tot_num):
        energies.append(MOs[i].eigenvalue)

    if res.occ_num is not None:
        OccNum = []
        for i in MOindices:
            OccNum.append(res.occ_num[MO_type][i])

        while len(OccNum) < mo_tot_num:
            OccNum.append(0.)

    MoMatrix = []
    sym0 = [i.sym for i in res.mo_sets[MO_type]]
    sym = [i.sym for i in res.mo_sets[MO_type]]
    for i in xrange(len(sym)):
        sym[MOmap[i]] = sym0[i]

    MoMatrix = []
    for i in xrange(len(MOs)):
        m = MOs[i]
        for coef in m.vector:
            MoMatrix.append(coef)

    while len(MoMatrix) < len(MOs[0].vector)**2:
        MoMatrix.append(0.)

    # ~#~#~#~#~ #
    # W r i t e #
    # ~#~#~#~#~ #

    ezfio.set_mo_basis_mo_tot_num(mo_tot_num)
    ezfio.set_mo_basis_mo_occ(OccNum)
    ezfio.set_mo_basis_mo_coef(MoMatrix)

    try:
        lmax = 0
        nucl_charge_remove = []
        klocmax = 0
        kmax = 0
        nucl_num = len(res.geometry)
        for ecp in res.pseudo:
          lmax_local = ecp['lmax']
          lmax = max(lmax_local,lmax)
          nucl_charge_remove.append(ecp['zcore'])
          klocmax = max(klocmax, len(ecp[str(lmax_local)]))
          for l in range(lmax_local):
            kmax = max(kmax,len(ecp[str(l)]))
        lmax = lmax-1
        ezfio.set_pseudo_pseudo_lmax(lmax)
        ezfio.set_pseudo_nucl_charge_remove(nucl_charge_remove)
        ezfio.set_pseudo_pseudo_klocmax(klocmax)
        ezfio.set_pseudo_pseudo_kmax(kmax)
        pseudo_n_k   = [   [ 0  for _ in range(nucl_num) ] for _ in range(klocmax) ]
        pseudo_v_k   = [   [ 0. for _ in range(nucl_num) ] for _ in range(klocmax) ]
        pseudo_dz_k  = [   [ 0. for _ in range(nucl_num) ] for _ in range(klocmax) ]
        pseudo_n_kl  = [ [ [ 0  for _ in range(nucl_num) ] for _ in range(kmax) ] for _ in range(lmax+1) ]
        pseudo_v_kl  = [ [ [ 0. for _ in range(nucl_num) ] for _ in range(kmax) ] for _ in range(lmax+1) ]
        pseudo_dz_kl = [ [ [ 0. for _ in range(nucl_num) ] for _ in range(kmax) ] for _ in range(lmax+1) ]
        for ecp in res.pseudo:
          lmax_local = ecp['lmax']
          klocmax = len(ecp[str(lmax_local)])
          atom = ecp['atom']-1
          for kloc in range(klocmax):
            try:
                v, n, dz = ecp[str(lmax_local)][kloc]
                pseudo_n_k[kloc][atom] = n-2
                pseudo_v_k[kloc][atom] = v
                pseudo_dz_k[kloc][atom] = dz
            except:
                pass
          for l in range(lmax_local):
            for k in range(kmax):
              try:
                v, n, dz = ecp[str(l)][k]
                pseudo_n_kl[l][k][atom] = n-2
                pseudo_v_kl[l][k][atom] = v
                pseudo_dz_kl[l][k][atom] = dz
              except:
                pass
        ezfio.set_pseudo_pseudo_n_k(pseudo_n_k)
        ezfio.set_pseudo_pseudo_v_k(pseudo_v_k)
        ezfio.set_pseudo_pseudo_dz_k(pseudo_dz_k)
        ezfio.set_pseudo_pseudo_n_kl(pseudo_n_kl)
        ezfio.set_pseudo_pseudo_v_kl(pseudo_v_kl)
        ezfio.set_pseudo_pseudo_dz_kl(pseudo_dz_kl)

        n_alpha = res.num_alpha
        n_beta  = res.num_beta
        for i in range(nucl_num):
          charge[i] -= nucl_charge_remove[i]
          n_alpha -= nucl_charge_remove[i]/2
          n_beta -= nucl_charge_remove[i]/2
        ezfio.set_nuclei_nucl_charge(charge)
        ezfio.set_electrons_elec_alpha_num(n_alpha)
        ezfio.set_electrons_elec_beta_num(n_beta)
    
    except:
        ezfio.set_pseudo_do_pseudo(False)
    else:
        ezfio.set_pseudo_do_pseudo(True)

        


def get_full_path(file_path):
    file_path = os.path.expanduser(file_path)
    file_path = os.path.expandvars(file_path)
    file_path = os.path.abspath(file_path)
    return file_path


if __name__ == '__main__':
    arguments = docopt(__doc__)

    file_ = get_full_path(arguments['<file.out>'])

    if arguments["-o"]:
        ezfio_file = get_full_path(arguments["<ezfio_directory>"])
    else:
        ezfio_file = "{0}.ezfio".format(file_)

    try:
        res_file = getFile(file_)
    except:
        raise
    else:
        print file_, 'recognized as', str(res_file).split('.')[-1].split()[0]

    write_ezfio(res_file, ezfio_file)
    if os.system("qp_run save_ortho_mos "+ezfio_file) != 0:
      print """Warning: You need to run 

         qp_run save_ortho_mos """+ezfio_file+"""

to be sure your MOs will be orthogonal, which is not the case when
the MOs are read from output files (not enough precision in output)."""


