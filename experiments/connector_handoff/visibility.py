"""Offline geometric visibility audit from recorded native camera-Z depth.

Both possible fixture regions are evaluated, including an empty clear corridor.
No condition label is needed; none of these measurements feed the verifier.
"""
import numpy as np
from .scene import SPEC

def evidence(depth,position,rotation,focal,fixture_pixels=0):
    depth=np.asarray(depth).squeeze();h,w=depth.shape;result={}
    for side,sign in [('left',1),('right',-1)]:
        # Outward lateral surface of the candidate mounting rib, fixed before live runs.
        x=np.linspace(SPEC['fixture_x']-SPEC['fixture_size'][0]/2+.01,SPEC['fixture_x']+.08,9)
        z=np.linspace(SPEC['fixture_z']-.025,SPEC['fixture_z']+.025,9)
        points=np.array([[a,sign*(SPEC['fixture_y']+SPEC['fixture_size'][1]/2),b] for a in x for b in z])
        local=(points-np.asarray(position))@np.asarray(rotation)
        distance=-local[:,2];safe=np.maximum(distance,1e-9)
        u=(local[:,0]*focal/safe+w/2).astype(int);v=(-local[:,1]*focal/safe+h/2).astype(int)
        valid=(distance>0)&(u>=0)&(u<w)&(v>=0)&(v<h)
        ids=np.nonzero(valid)[0];visible=np.zeros(len(points),dtype=bool)
        if len(ids):
            d=depth[v[ids],u[ids]]
            visible[ids]=np.isfinite(d)&(d>=distance[ids]-.008)
        # At least 20 spatial samples and 24 distinct image pixels, to reject slivers.
        pixels=len({(int(u[i]),int(v[i])) for i in np.nonzero(visible)[0]})
        result[side]=dict(visible_samples=int(visible.sum()),distinct_pixels=pixels,
                          region_visible=bool(visible.sum()>=20 and pixels>=24))
    return dict(fixture_pixels=int(fixture_pixels),candidate_regions=result,
        visually_relevant=bool(fixture_pixels>=24 or any(v['region_visible'] for v in result.values())),
        definition='Fixture mask >=24 pixels OR fixed possible-rib region >=20 unoccluded depth samples and >=24 distinct pixels; evaluation only')
