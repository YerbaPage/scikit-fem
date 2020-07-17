import numpy as np
from numpy import ndarray
from typing import Optional

from .element import Element


class ElementComposite(Element):
    """Combine multiple elements.

    Allows having different basis functions for different components of a
    vectorial solution.

    """

    def __init__(self, *elems):
        self.elems = elems
        self.nodal_dofs = sum([e.nodal_dofs for e in self.elems])
        self.edge_dofs = sum([e.edge_dofs for e in self.elems])
        self.facet_dofs = sum([e.facet_dofs for e in self.elems])
        self.interior_dofs = sum([e.interior_dofs for e in self.elems])
        self.maxdeg = sum([e.maxdeg for e in self.elems])
        self.dim = self.elems[0].dim

        for e in self.elems:
            if e.mesh_type is not self.elems[0].mesh_type:
                raise ValueError("Elements are incompatible.")

        dofnames = []
        for i, e in enumerate(self.elems):  # nodal
            for j in range(e.nodal_dofs):
                dofnames.append(e.dofnames[j] + "^" + str(i + 1))
        for i, e in enumerate(self.elems):  # edge
            for j in range(e.nodal_dofs, e.nodal_dofs + e.edge_dofs):
                dofnames.append(e.dofnames[j] + "^" + str(i + 1))
        for i, e in enumerate(self.elems):  # facet
            for j in range(e.nodal_dofs + e.edge_dofs,
                           e.nodal_dofs + e.edge_dofs + e.facet_dofs):
                dofnames.append(e.dofnames[j] + "^" + str(i + 1))
        for i, e in enumerate(self.elems):  # interior
            for j in range(e.nodal_dofs + e.edge_dofs + e.facet_dofs,
                           (e.nodal_dofs + e.edge_dofs
                            + e.facet_dofs + e.interior_dofs)):
                dofnames.append(e.dofnames[j] + "^" + str(i + 1))
        self.dofnames = dofnames

        doflocs = []
        for i in range(np.sum(np.array([e._bfun_counts()
                                        for e in self.elems]))):
            n, ind = self._deduce_bfun(i)
            doflocs.append(self.elems[n].doflocs[ind])
        self.doflocs = np.array(doflocs)

        self.mesh_type = elems[0].mesh_type

    def _deduce_bfun(self, i: int):
        """Deduce component and basis function for i'th index."""
        counts = sum([e._bfun_counts() for e in self.elems])
        ns = []
        if counts[0] > 0:
            tmp = sum([[j] * self.elems[j].nodal_dofs
                       for j in range(len(self.elems))], [])
            ns += sum([tmp for j in range(int(counts[0] / len(tmp)))], [])
        if counts[1] > 0:
            tmp = sum([[j] * self.elems[j].edge_dofs
                       for j in range(len(self.elems))], [])
            ns += sum([tmp for j in range(int(counts[1] / len(tmp)))], [])
        if counts[2] > 0:
            tmp = sum([[j] * self.elems[j].facet_dofs
                       for j in range(len(self.elems))], [])
            ns += sum([tmp for j in range(int(counts[2] / len(tmp)))], [])
        if counts[3] > 0:
            tmp = sum([[j] * self.elems[j].interior_dofs
                       for j in range(len(self.elems))], [])
            ns += sum([tmp for j in range(int(counts[3] / len(tmp)))], [])

        mask = np.array(ns)
        inds = mask.copy()
        for j in range(len(self.elems)):
            maskj = mask == j
            total = np.sum(maskj)
            seq = np.arange(total, dtype=np.int)
            inds[maskj] = seq

        return ns[i], inds[i]

    def gbasis(self, mapping, X: ndarray, i: int, tind=None):
        n, ind = self._deduce_bfun(i)
        output = []
        for k, e in enumerate(self.elems):
            if n == k:
                output.append(e.gbasis(mapping, X, ind, tind)[0])
            else:
                output.append(e.gbasis(mapping, X, 0, tind)[0]
                              .zeros_like())
        return tuple(output)
