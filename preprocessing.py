import logging
import os
import glob
import sys
import functools
from typing import List

import snappy
from snappy import ProductIO, Product, ProductData, ProductUtils, String
from snappy import HashMap, GPF

def load_file() -> List[str]:
    """
    Load the product file with the .N1 extension from the .snap/snap-python directory.
    Raises a RuntimeError if the directory is not found.
    Returns a list of file paths with the .N1 extension.
    """
    snappy_dir = os.path.join(os.path.expanduser("~"), ".snap", "snap-python")
    if not os.path.isdir(snappy_dir):
        raise RuntimeError("The directory {snappy_dir} was not found. Please make sure that the SNAP software is installed and that the .snap/snap-python directory exists.")

    file_paths = glob.glob(os.path.join(snappy_dir, '*.N1'))
    if not file_paths:
        raise RuntimeError("No product files found in .snap/snap-python directory")

    return file_paths


def read_product() -> Product:
    """
    Read the product from the first file with the .N1 extension in the .snap/snap-python directory.
    Raises a RuntimeError if the product cannot be read.
    Returns the Product object.
    """    
    file_paths = load_file()
    if not file_paths:
        raise RuntimeError("No product files found in .snap/snap-python directory")
    product_path = file_paths[0]
    
    try:
        product = ProductIO.readProduct(product_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read product file {product_path}: {str(e)}")

    return product


def apply_orbit_file() -> Product:   
    """
    Apply the orbit file to the product.
    Returns the Product object with the orbit file applied.
    """   
    source = read_product()
    parameters = HashMap()
    parameters.put('Apply-Orbit-File', True)
    return GPF.createProduct('Apply-Orbit-File', parameters, source)


def linear_to_dB(func):
    """
    A decorator that applies the 'linearToFromdB' operator to the product returned by the decorated function.
    Args:
        func: The function to be decorated.
    Returns:
        A new function that applies the 'linearToFromdB' operator to the product returned by the decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        product = func(*args, **kwargs)
        parameters = HashMap()
        parameters.put('sourceProduct', product)
        parameters.put('targetBandNames', 'Sigma0_HH')
        return GPF.createProduct('linearToFromdB', parameters, product)
    return wrapper

def calibrate_amplitude() -> Product:
    """
    Applies the 'Calibration' operator to the product returned by the 'apply_orbit_file' function, using the
    polarization metadata attribute to select the appropriate polarizations.
    """
    orbit = apply_orbit_file()
    polarization = orbit.getMetadataRoot().getElement('Abstracted_Metadata').getAttributeString('MDS1_TX_RX_POLAR')

    polarizations_dict = {'DV': 'VH,VV', 'DH': 'HH,HV', 'SH': 'HH', 'HH': 'HH', 'SV': 'VV'}
    if polarization not in polarizations_dict:
        raise ValueError(f"Invalid polarization value: {polarization}. Valid values are {', '.join(polarizations_dict.keys())}")
    
    parameters = HashMap()
    parameters.put('outputSigmaBand', True)
    parameters.put('selectedPolarisations', polarizations_dict[polarization])
    parameters.put('outputImageScaleInDb', False)

    product = GPF.createProduct("Calibration", parameters, orbit)
    return product

@linear_to_dB
def amplitude_db():
    """
    A decorator function that calibrates the input product and then applies the 'linearToFromdB' operator to the
    'Sigma0_HH' band.
    """    
    return calibrate_amplitude()

def correct_angle(db=True) -> Product:
    product = amplitude_db() if db else calibrate_amplitude()
    
    band_name = product.getBands()[0].getName()
    print(band_name)
    
    if ('Sigma0_HH' or 'Sigma0_HH_db') not in band_name:
        print('Angular correction must be applied only for HH-pol')
        
    elif 'Sigma0_HH_db' in band_name:
        expr = "(Sigma0_HH_db) - (-0.247) * (incident_angle - 25)"
        
    else:
        expr = "10 * log10(Sigma0_HH) - (-0.24) * (incident_angle - 25)"       
        
    BandDescriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
    targetBand = BandDescriptor()
    targetBand.name = 'Sigma0_HH_db_corrected'
    targetBand.type = 'float32'
    targetBand.expression = expr
    
    targetBands = jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
    targetBands[0] = targetBand

    parameters = HashMap()
    parameters.put('targetBands', targetBands)

    return GPF.createProduct('BandMaths', parameters, product)

def write_file(ext='GeoTIFF', db=True):
    """
    Writes a corrected SAR product to a file.

    Args:
        ext (str): The file format extension to use. Default is 'GeoTIFF'.
        db (bool): Whether to use amplitude values in decibels (True) or linear values (False). Default is True.
    """    
    source = correct_angle(db)

    dir_name = ext.upper()
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    
    outpath = os.path.join(os.path.abspath('.'), dir_name, source.getName())
    
    try:
        ProductIO.writeProduct(source, outpath, ext)
        print(f'Product written to {outpath} in {ext} format.')
    except Exception as e:
        logging.error(f'Error writing product to file: {str(e)}')

# Correct angle with linearToFromdB
#correct_angle() # This will use the default value of db=True

<<<<<<< HEAD
# Correct angle with linearToFromdB
#correct_angle() # This will use the default value of db=True

# Correct angle without linearToFromdB
correct_angle(db=False)



=======
# Correct angle without linearToFromdB
correct_angle(db=False)
>>>>>>> 1dcb095f04dc0f5758ca09d630e312148a2811e0
