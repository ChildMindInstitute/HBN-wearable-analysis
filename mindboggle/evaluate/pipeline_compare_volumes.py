#!/usr/bin/python
"""
This is a Nipype pipeline for comparing nibabel-readable image volumes.


Authors:
    - Arno Klein  (arno@mindboggle.info)  http://binarybottle.com

Copyright 2012,  Mindboggle team (http://mindboggle.info), Apache v2.0 License

"""
import os

#=============================================================================
# Setup: import libraries, set file paths, and initialize main workflow
#=============================================================================
#-----------------------------------------------------------------------------
# Data to run
#-----------------------------------------------------------------------------
run_test_retest_humans = False
run_structural_phantoms = True
run_DTI_phantoms = 0 #True
#-----------------------------------------------------------------------------
# Steps to run
#-----------------------------------------------------------------------------
do_register_images_to_first_image = True
do_threshold_images = True
do_compute_image_similarities = True
do_compare_image_histograms = True
do_compute_image_overlaps = False  # Not as useful
#-----------------------------------------------------------------------------
# Paths and images to process
#-----------------------------------------------------------------------------
# images_path is the beginning of the path not in the text of image_list file
data_path = '/drop/EMBARC/Data'
results_path = '/drop/EMBARC/Results'
temp_path = '/desk'
if run_test_retest_humans:
    output_path = 'Human_retests'
    images_path = 'Human_retests'
    image_list = 'Human_retests.txt'
    temp_path = os.path.join(temp_path, 'workspace_humans')
    threshold_value = 0.1
elif run_structural_phantoms:
    output_path = 'ADNI_phantoms'
    images_path = 'Phantom_ADNI_Updated20121213'
    image_list = 'Phantom_ADNI.txt'
    temp_path = os.path.join(temp_path, 'workspace_ADNI')
    threshold_value = 0.1
elif run_DTI_phantoms:
    output_path = 'DTI_phantoms'
    images_path = 'Phantom_DTI_Updated20121214'
    image_list = 'Phantom_DTI_FA.txt'
    image_list_ref = 'Phantom_DTI_1stVol.txt'
    temp_path = os.path.join(temp_path, 'workspace_DTI')
    threshold_value = 0.3
images_path = os.path.join(data_path, images_path)
image_list = os.path.join(images_path, image_list)
if run_DTI_phantoms:
    image_list_ref = os.path.join(images_path, image_list_ref)
output_path = os.path.join(results_path, output_path)
#-----------------------------------------------------------------------------
# Import system and nipype Python libraries
#-----------------------------------------------------------------------------
from nipype.pipeline.engine import Workflow, Node
from nipype.interfaces.utility import Function as Fn
from nipype.interfaces.io import DataSink
#from nipype.interfaces.utility import IdentityInterface
#-----------------------------------------------------------------------------
# Import Mindboggle Python libraries
#-----------------------------------------------------------------------------
from mindboggle.measure.measure_functions import pairwise_vector_distances
from mindboggle.evaluate.compare_images import compute_image_histograms, \
    compute_image_similarities, compute_image_overlaps, \
    register_images_to_first_image, apply_transforms, threshold_images
#-------------------------------------------------------------------------------
# Initialize workflows
#-------------------------------------------------------------------------------
Flow = Workflow(name='Image_comparison_workflow')
Flow.base_dir = temp_path
if not os.path.isdir(temp_path):
    os.makedirs(temp_path)
#-----------------------------------------------------------------------------
# Inputs and Outputs
#-----------------------------------------------------------------------------
if run_test_retest_humans:
    threshold_value = 0.1
elif run_structural_phantoms:
    threshold_value = 0.1
elif run_DTI_phantoms:
    fid_ref = open(image_list_ref)
    file_list_ref = fid_ref.read()
    file_list_ref = file_list_ref.splitlines()
    file_list_ref = [x.strip() for x in file_list_ref if len(x)]
    threshold_value = 0.3
fid = open(image_list)
file_list = fid.read()
file_list = file_list.splitlines()
file_list = [x.strip() for x in file_list if len(x)]
if run_DTI_phantoms:
    fid_ref = open(image_list_ref)
    file_list_ref = fid_ref.read()
    file_list_ref = file_list_ref.splitlines()
    file_list_ref = [x.strip() for x in file_list_ref if len(x)]
#Info = Node(name = 'Inputs',
#            interface = IdentityInterface(fields=['files']))
#Info.iterables = ([('files', file_list)])
Sink = Node(DataSink(), name = 'Results')
Sink.inputs.base_directory = output_path
Sink.inputs.container = 'Results'
if not os.path.isdir(output_path):  os.makedirs(output_path)

#=============================================================================
#   Comparisons
#=============================================================================
#-------------------------------------------------------------------------------
# Compare image histograms
# The images from which the histograms were derived do not need to be coregistered.
#-------------------------------------------------------------------------------
if do_compare_image_histograms:
    compute_histograms = Node(name = 'Compute_histograms',
                              interface = Fn(function = compute_image_histograms,
                                             iterfield=['infiles'],
                                             input_names = ['infiles',
                                                            'indirectory',
                                                            'nbins',
                                                            'threshold'],
                                             output_names = ['histogram_values']))
    Flow.add_nodes([compute_histograms])
    compute_histograms.inputs.infiles = file_list
    compute_histograms.inputs.indirectory = images_path
    compute_histograms.inputs.nbins = 100
    compute_histograms.inputs.threshold = 0

    compare_histograms = Node(name = 'Compare_histograms',
                              interface = Fn(function = pairwise_vector_distances,
                                             input_names = ['vectors',
                                                            'save_file',
                                                            'normalize'],
                                             output_names = ['vector_distances',
                                                             'outfile']))
    Flow.add_nodes([compare_histograms])
    Flow.connect([(compute_histograms, compare_histograms,
                   [('histogram_values','vectors')])])
    compare_histograms.inputs.save_file = True
    compare_histograms.inputs.normalize = True

    Flow.connect([(compare_histograms, Sink, [('outfile', 'histograms')])])

#-------------------------------------------------------------------------------
# Register images to first_image
#-------------------------------------------------------------------------------
if do_register_images_to_first_image:
    register = Node(name = 'Register',
                    interface = Fn(function = register_images_to_first_image,
                                   input_names = ['files',
                                                  'directory'],
                                   output_names = ['outfiles']))
    Flow.add_nodes([register])
    if run_test_retest_humans:
        register.inputs.files = file_list
    elif run_structural_phantoms:
        register.inputs.files = file_list
    elif run_DTI_phantoms:
        register.inputs.files = file_list_ref
    register.inputs.directory = images_path
    #Flow.connect([(register, Sink, [('outfiles', 'registrations.@transforms')])])

    transform = Node(name = 'Transform',
                    interface = Fn(function = apply_transforms,
                                   input_names = ['image_files',
                                                  'transform_files',
                                                  'directory'],
                                   output_names = ['outfiles']))
    Flow.add_nodes([transform])
    transform.inputs.image_files = file_list
    Flow.connect([(register, transform, [('outfiles', 'transform_files')])])
    transform.inputs.directory = images_path
    Flow.connect([(transform, Sink, [('outfiles', 'registrations.@images')])])

#-------------------------------------------------------------------------------
# Threshold images
#-------------------------------------------------------------------------------
if do_threshold_images:
    threshold = Node(name = 'Threshold',
                     interface = Fn(function = threshold_images,
                                    input_names = ['files',
                                                   'threshold_value',
                                                   'save_files'],
                                    output_names = ['outfiles']))
    Flow.add_nodes([threshold])
    Flow.connect([(transform, threshold, [('outfiles', 'files')])])
    threshold.inputs.threshold_value = threshold_value
    threshold.inputs.save_files = True
    Flow.connect([(threshold, Sink, [('outfiles', 'thresholds')])])

#-------------------------------------------------------------------------------
# Compute image similarities
#-------------------------------------------------------------------------------
if do_compute_image_similarities:
    similarity = Node(name = 'Similarity',
                      interface = Fn(function = compute_image_similarities,
                                    input_names = ['files',
                                                   'masks',
                                                   'metric',
                                                   'save_file'],
                                    output_names = ['pairwise_similarities',
                                                    'outfile']))
    Flow.add_nodes([similarity])
    Flow.connect([(transform, similarity, [('outfiles', 'files')])])
    Flow.connect([(threshold, similarity, [('outfiles', 'masks')])])
    similarity.inputs.metric = 'cc'
    similarity.inputs.save_file = True
    Flow.connect([(similarity, Sink, [('outfile', 'similarities')])])

#-------------------------------------------------------------------------------
# Compute image overlaps
#-------------------------------------------------------------------------------
if do_compute_image_overlaps:
    overlaps = Node(name = 'Overlaps',
                     interface = Fn(function = compute_image_overlaps,
                                    input_names = ['files',
                                                   'list_of_labels',
                                                   'save_file'],
                                    output_names = ['pairwise_overlaps',
                                                    'outfile']))
    Flow.add_nodes([overlaps])
    Flow.connect([(threshold, overlaps, [('outfiles', 'files')])])
    overlaps.inputs.list_of_labels = [1]
    overlaps.inputs.save_file = True
    Flow.connect([(overlaps, Sink, [('outfile', 'overlaps')])])

##############################################################################
if __name__== '__main__':
    #Flow.write_graph(graph2use='flat')
    #Flow.write_graph(graph2use='hierarchical')
    Flow.run()
