/**
 * Minecraft Bedrock Low 32-bit Seed Cracker - OpenCL Host Code
 *
 * This file provides the CPU-side code to launch GPU computation.
 * Supports both Bedrock MT19937 and Java LCG random number generators.
 *
 * Compile (Windows):
 *   gcc -O3 -shared -o crack_low32_opencl.dll crack_low32_opencl.c -I"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.0\include" -L"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.0\lib\x64" -lOpenCL
 *
 * Compile (Linux):
 *   gcc -O3 -fPIC -shared -o crack_low32_opencl.so crack_low32_opencl.c -lOpenCL
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __APPLE__
#include <OpenCL/opencl.h>
#else
#include <CL/cl.h>
#endif

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

// Kernel source is loaded from file at runtime

// Debug output control (set to 1 to enable verbose output)
#define OPENCL_DEBUG 0

// Error checking macro
#define CL_CHECK(err, msg)       \
    do                           \
    {                            \
        if ((err) != CL_SUCCESS) \
        {                        \
            return -1;           \
        }                        \
    } while (0)

/**
 * Get device info string
 */
static void get_device_info(cl_device_id device, const char **name, const char **vendor)
{
    static char name_buf[256];
    static char vendor_buf[256];

    clGetDeviceInfo(device, CL_DEVICE_NAME, sizeof(name_buf), name_buf, NULL);
    clGetDeviceInfo(device, CL_DEVICE_VENDOR, sizeof(vendor_buf), vendor_buf, NULL);

    *name = name_buf;
    *vendor = vendor_buf;
}

/**
 * Check if OpenCL GPU is available
 * Returns: 1 if GPU available, 0 otherwise
 */
EXPORT int has_opencl_gpu()
{
    cl_platform_id platforms[8];
    cl_uint num_platforms;
    cl_int err;

    err = clGetPlatformIDs(8, platforms, &num_platforms);
    if (err != CL_SUCCESS || num_platforms == 0)
        return 0;

    for (cl_uint p = 0; p < num_platforms; p++)
    {
        cl_device_id devices[8];
        cl_uint num_devices;

        err = clGetDeviceIDs(platforms[p], CL_DEVICE_TYPE_GPU, 8, devices, &num_devices);
        if (err == CL_SUCCESS && num_devices > 0)
            return 1;
    }

    return 0;
}

/**
 * Get GPU compute units for dynamic scaling
 * Returns: number of compute units, or 0 if not available
 */
EXPORT int get_gpu_compute_units()
{
    cl_platform_id platforms[8];
    cl_uint num_platforms;
    cl_int err;

    err = clGetPlatformIDs(8, platforms, &num_platforms);
    if (err != CL_SUCCESS || num_platforms == 0)
        return 0;

    for (cl_uint p = 0; p < num_platforms; p++)
    {
        cl_device_id devices[8];
        cl_uint num_devices;

        err = clGetDeviceIDs(platforms[p], CL_DEVICE_TYPE_GPU, 8, devices, &num_devices);
        if (err == CL_SUCCESS && num_devices > 0)
        {
            cl_uint compute_units;
            err = clGetDeviceInfo(devices[0], CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cl_uint), &compute_units, NULL);
            if (err == CL_SUCCESS)
                return (int)compute_units;
        }
    }

    return 0;
}

/**
 * Get OpenCL device info string
 * Returns device name in the provided buffer
 */
EXPORT int get_opencl_device_info(char *buffer, int buffer_size)
{
    cl_platform_id platforms[8];
    cl_uint num_platforms;
    cl_int err;

    err = clGetPlatformIDs(8, platforms, &num_platforms);
    if (err != CL_SUCCESS || num_platforms == 0)
    {
        snprintf(buffer, buffer_size, "No OpenCL platform");
        return 0;
    }

    for (cl_uint p = 0; p < num_platforms; p++)
    {
        cl_device_id devices[8];
        cl_uint num_devices;

        err = clGetDeviceIDs(platforms[p], CL_DEVICE_TYPE_GPU, 8, devices, &num_devices);
        if (err == CL_SUCCESS && num_devices > 0)
        {
            const char *name, *vendor;
            get_device_info(devices[0], &name, &vendor);
            snprintf(buffer, buffer_size, "%s (%s)", name, vendor);
            return 1;
        }
    }

    snprintf(buffer, buffer_size, "No GPU found");
    return 0;
}

/**
 * Main crack function using OpenCL
 *
 * Parameters:
 *   start, end: Seed range to check
 *   r_base_bedrock: Structure r_base values for Bedrock MT (64-bit for compatibility)
 *   r_base_java: Structure r_base values for Java LCG (64-bit)
 *   ox, oz, offset_range: Structure position parameters
 *   spread_type: Structure spread type (0=linear, 1=triangular)
 *   rng_type: RNG type (0=bedrock MT, 1=java LCG)
 *   num_targets: Number of structures
 *   results: Output buffer for matching seeds
 *   max_results: Maximum number of results to store
 *
 * Returns: Number of matching seeds found, or -1 on error
 */
EXPORT int crack_low32_opencl(
    uint32_t start,
    uint32_t end,
    uint64_t *r_base_bedrock,
    uint64_t *r_base_java,
    uint32_t *ox,
    uint32_t *oz,
    uint32_t *offset_range,
    int *spread_type,
    int *rng_type,
    int num_targets,
    uint32_t *results,
    int max_results)
{
    cl_int err;
    cl_platform_id platform;
    cl_device_id device;
    cl_context context;
    cl_command_queue queue;
    cl_program program;
    cl_kernel kernel;

    // Get first available GPU
    err = clGetPlatformIDs(1, &platform, NULL);
    CL_CHECK(err, "clGetPlatformIDs");

    err = clGetDeviceIDs(platform, CL_DEVICE_TYPE_GPU, 1, &device, NULL);
    CL_CHECK(err, "clGetDeviceIDs");

    // Print device info
    const char *dev_name, *dev_vendor;
    get_device_info(device, &dev_name, &dev_vendor);
    // GPU device info logged only in debug mode
    // fprintf(stderr, "[OpenCL] Using GPU: %s (%s)\n", dev_name, dev_vendor);

    // Calculate total seeds and work configuration
    uint64_t total_seeds = (uint64_t)end - start + 1;

    // Get GPU compute units for dynamic scaling
    cl_uint compute_units = 4; // Default for old GPUs
    err = clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cl_uint), &compute_units, NULL);
    if (err != CL_SUCCESS)
        compute_units = 4;

    // Dynamic thread count based on GPU capability
    // Modern GPUs (100+ CUs): Use more threads
    // Old GPUs (<50 CUs): Use fewer threads to avoid timeout
    size_t base_threads;
    if (compute_units >= 100)
    {
        base_threads = 4096; // Modern high-end GPU
    }
    else if (compute_units >= 50)
    {
        base_threads = 2048; // Mid-range GPU
    }
    else if (compute_units >= 20)
    {
        base_threads = 1024; // Low-end modern GPU
    }
    else
    {
        base_threads = compute_units * 8; // Very old GPU (GTX 550 Ti: 4 CUs -> 32 threads)
        if (base_threads < 32)
            base_threads = 32; // Minimum 32 threads
    }

    // Limit maximum threads for stability
    const size_t MAX_THREADS = 8192;
    if (base_threads > MAX_THREADS)
        base_threads = MAX_THREADS;

    // Calculate seeds per thread
    uint32_t seeds_per_thread = (uint32_t)((total_seeds + base_threads - 1) / base_threads);

    // If each thread needs to check too many seeds, use batch processing
    // GPU kernel should complete within ~1 second to avoid TDR
    // For old GPUs with limited resources, use very conservative limit
    const uint32_t MAX_SEEDS_PER_THREAD_MODERN = 500000; // Modern GPU (RTX/GTX 10-series+)
    const uint32_t MAX_SEEDS_PER_THREAD_OLD = 50000;     // Old GPU (GTX 9-series)
    const uint32_t MAX_SEEDS_PER_THREAD_ANCIENT = 5000;  // Ancient GPU (Fermi/Kepler like GTX 550 Ti)

    uint32_t max_seeds_per_thread;
    if (compute_units >= 20)
    {
        max_seeds_per_thread = MAX_SEEDS_PER_THREAD_MODERN;
    }
    else if (compute_units >= 10)
    {
        max_seeds_per_thread = MAX_SEEDS_PER_THREAD_OLD;
    }
    else
    {
        max_seeds_per_thread = MAX_SEEDS_PER_THREAD_ANCIENT;
    }

    int use_batch_mode = 0;
    if (seeds_per_thread > max_seeds_per_thread)
    {
        use_batch_mode = 1;
        seeds_per_thread = max_seeds_per_thread;
    }

    size_t global_work_size = base_threads;

    // Create context and command queue
    context = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    CL_CHECK(err, "clCreateContext");

    queue = clCreateCommandQueue(context, device, CL_QUEUE_PROFILING_ENABLE, &err);
    CL_CHECK(err, "clCreateCommandQueue");

    // Create program from kernel source
    FILE *fp = fopen("crack_low32.cl", "r");
    if (!fp)
    {
        // Error: cannot open kernel file
        clReleaseCommandQueue(queue);
        clReleaseContext(context);
        return -1;
    }

    fseek(fp, 0, SEEK_END);
    size_t kernel_size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    char *kernel_source = (char *)malloc(kernel_size + 1);
    fread(kernel_source, 1, kernel_size, fp);
    kernel_source[kernel_size] = '\0';
    fclose(fp);

    const char *source_ptr = kernel_source;
    program = clCreateProgramWithSource(context, 1, &source_ptr, &kernel_size, &err);
    CL_CHECK(err, "clCreateProgramWithSource");

    // Build program
    err = clBuildProgram(program, 1, &device, "-cl-std=CL1.1", NULL, NULL);
    if (err != CL_SUCCESS)
    {
        // Print build log on failure
        clReleaseProgram(program);
        clReleaseCommandQueue(queue);
        clReleaseContext(context);
        free(kernel_source);
        return -1;
    }

    // Create kernel
    kernel = clCreateKernel(program, "crack_low32_kernel", &err);
    CL_CHECK(err, "clCreateKernel");

    // Create buffers
    cl_mem results_buffer = clCreateBuffer(context, CL_MEM_WRITE_ONLY, sizeof(uint32_t) * max_results, NULL, &err);
    CL_CHECK(err, "clCreateBuffer results");

    cl_mem count_buffer = clCreateBuffer(context, CL_MEM_READ_WRITE, sizeof(uint32_t), NULL, &err);
    CL_CHECK(err, "clCreateBuffer count");

    cl_mem r_base_bedrock_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint64_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer r_base_bedrock");

    cl_mem r_base_java_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint64_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer r_base_java");

    cl_mem ox_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer ox");

    cl_mem oz_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer oz");

    cl_mem offset_range_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer offset_range");

    cl_mem spread_type_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(int) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer spread_type");

    cl_mem rng_type_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(int) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer rng_type");

    // Initialize result count to 0
    uint32_t zero = 0;
    err = clEnqueueWriteBuffer(queue, count_buffer, CL_TRUE, 0, sizeof(uint32_t), &zero, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer count init");

    // Write input data
    err = clEnqueueWriteBuffer(queue, r_base_bedrock_buffer, CL_TRUE, 0, sizeof(uint64_t) * num_targets, r_base_bedrock, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer r_base_bedrock");

    err = clEnqueueWriteBuffer(queue, r_base_java_buffer, CL_TRUE, 0, sizeof(uint64_t) * num_targets, r_base_java, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer r_base_java");

    err = clEnqueueWriteBuffer(queue, ox_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, ox, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer ox");

    err = clEnqueueWriteBuffer(queue, oz_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, oz, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer oz");

    err = clEnqueueWriteBuffer(queue, offset_range_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, offset_range, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer offset_range");

    err = clEnqueueWriteBuffer(queue, spread_type_buffer, CL_TRUE, 0, sizeof(int) * num_targets, spread_type, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer spread_type");

    err = clEnqueueWriteBuffer(queue, rng_type_buffer, CL_TRUE, 0, sizeof(int) * num_targets, rng_type, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer rng_type");

    // Set kernel arguments
    // Note: parameter order changed - now using end_seed instead of total_seeds to avoid overflow
    err = clSetKernelArg(kernel, 0, sizeof(cl_mem), &results_buffer);
    err |= clSetKernelArg(kernel, 1, sizeof(cl_mem), &count_buffer);
    err |= clSetKernelArg(kernel, 2, sizeof(uint32_t), &start);
    err |= clSetKernelArg(kernel, 3, sizeof(uint32_t), &end); // Pass end directly instead of total_seeds
    err |= clSetKernelArg(kernel, 4, sizeof(uint32_t), &seeds_per_thread);
    err |= clSetKernelArg(kernel, 5, sizeof(cl_mem), &r_base_bedrock_buffer);
    err |= clSetKernelArg(kernel, 6, sizeof(cl_mem), &r_base_java_buffer);
    err |= clSetKernelArg(kernel, 7, sizeof(cl_mem), &ox_buffer);
    err |= clSetKernelArg(kernel, 8, sizeof(cl_mem), &oz_buffer);
    err |= clSetKernelArg(kernel, 9, sizeof(cl_mem), &offset_range_buffer);
    err |= clSetKernelArg(kernel, 10, sizeof(cl_mem), &spread_type_buffer);
    err |= clSetKernelArg(kernel, 11, sizeof(cl_mem), &rng_type_buffer);
    err |= clSetKernelArg(kernel, 12, sizeof(uint32_t), &num_targets);
    err |= clSetKernelArg(kernel, 13, sizeof(uint32_t), &max_results);
    CL_CHECK(err, "clSetKernelArg");

    // Execute kernel
    err = clEnqueueNDRangeKernel(queue, kernel, 1, NULL, &global_work_size, NULL, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueNDRangeKernel");

    // Wait for completion
    err = clFinish(queue);
    CL_CHECK(err, "clFinish");

    // Read results
    uint32_t result_count;
    err = clEnqueueReadBuffer(queue, count_buffer, CL_TRUE, 0, sizeof(uint32_t), &result_count, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueReadBuffer count");

    if (result_count > max_results)
        result_count = max_results;

    err = clEnqueueReadBuffer(queue, results_buffer, CL_TRUE, 0, sizeof(uint32_t) * result_count, results, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueReadBuffer results");

    // Cleanup
    clReleaseMemObject(results_buffer);
    clReleaseMemObject(count_buffer);
    clReleaseMemObject(r_base_bedrock_buffer);
    clReleaseMemObject(r_base_java_buffer);
    clReleaseMemObject(ox_buffer);
    clReleaseMemObject(oz_buffer);
    clReleaseMemObject(offset_range_buffer);
    clReleaseMemObject(spread_type_buffer);
    clReleaseMemObject(rng_type_buffer);
    clReleaseKernel(kernel);
    clReleaseProgram(program);
    clReleaseCommandQueue(queue);
    clReleaseContext(context);
    free(kernel_source);

    return (int)result_count;
}