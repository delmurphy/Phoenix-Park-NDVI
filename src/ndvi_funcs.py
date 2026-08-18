# Load packages
# import geopandas as gpd
import rioxarray
from odc.stac import load
import numpy as np
# import pystac_client
import planetary_computer
# import xarray as xr
import matplotlib.pyplot as plt

def calculate_scene_ndvi(item, park_utm):
    """ Calculates mean NDVI for the whole park for a given year and 
        also returns NDVI values per pixel that is defined as vegetation"""

    # sign item:
    item = planetary_computer.sign(item)

    xmin, ymin, xmax, ymax = park_utm.total_bounds

    # load three bands (NIR, Red, SCL) from STAC item
    ds = load(
        [item],
        bands=["B04", "B08", "SCL"],
        crs="EPSG:32629",
        resolution=10,
        x=(xmin, xmax),
        y=(ymin,ymax)
    )

    # crop to park bounding box
    # xmin, ymin, xmax, ymax = park_utm.total_bounds
    park_bbox = ds.sel(
        x = slice(xmin, xmax),
        y = slice(ymax, ymin)
    )

    # mask to park geometry
    park_bbox = park_bbox.rio.write_crs("EPSG:32629")
    park_masked = park_bbox.rio.clip(
        park_utm.geometry,
        park_utm.crs, 
        drop=False 
    )

    # keep vegetation pixels
    vegetation_classes = [4]
    vegetation_mask = park_masked.SCL.isin(vegetation_classes)

    # calculate NDVI per pixel
    red = park_masked.B04.where(vegetation_mask)
    nir = park_masked.B08.where(vegetation_mask)
    ndvi = (
        (nir - red)
        / (nir + red)
    )

    # calculate mean NDVI
    ndvi_mean = ndvi.mean().item()

    # calculate vegetation pixels
    veg_pixels = vegetation_mask.sum().item()

    # return mean NDVI
    return (
        ndvi_mean, 
        veg_pixels,
        ndvi.squeeze("time")
        )




def plot_ndvi_map(year, park_utm, annual_median_ndvi, annual_maps, ax, vmin, vmax):
    """ Plots mean NDVI values per vegetation pixel inside the park"""

    # fig, ax = plt.subplots(figsize=(10, 6))

    annual_maps[year].squeeze().plot(
        ax=ax,
        cmap="RdYlGn",
        vmin=vmin,
        vmax=vmax,
        add_colorbar=False
    )

    park_utm.boundary.plot(
        ax=ax,
        color="black",
        linewidth=2
    )

    median_ndvi = annual_median_ndvi.loc[year]

    # ax.set_title(f"July NDVI {year} (mean values per 100 m²)")
    ax.set_title(f"{year}")

    ax.text(
        0.62,
        0.98,
        f"Median NDVI: {median_ndvi:.2f}",
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment="top",
        bbox=dict(facecolor="white", alpha=0.8)
    )

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
