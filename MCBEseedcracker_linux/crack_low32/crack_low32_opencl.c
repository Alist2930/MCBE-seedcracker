/**
 * Minecraft Bedrock Low 32-bit Seed Cracker - OpenCL Host Code (Linux)
 *
 * Compile:
 *   gcc -O3 -fPIC -shared -o crack_low32_opencl.so crack_low32_opencl.c -lOpenCL
 *
 * Usage:
 *   python crack_low32.py              # Auto-detect GPU/CPU
 *   python crack_low32.py --gpu        # Force GPU mode
 *   python crack_low32.py --cpu        # Force CPU mode
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <CL/cl.h>

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
int has_opencl_gpu()
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
int get_gpu_compute_units()
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
int get_opencl_device_info(char *buffer, int buffer_size)
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
 */
int crack_low32_opencl(
    uint32_t start,
    uint32_t end,
    uint32_t *r_base,
    uint32_t *ox,
    uint32_t *oz,
    uint32_t *offset_range,
    int *spread_type,
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

    // Get device info (for internal use)
    const char *dev_name, *dev_vendor;
    get_device_info(device, &dev_name, &dev_vendor);

    // Calculate total seeds and work configuration
    uint64_t total_seeds = (uint64_t)end - start + 1;

    // Get GPU compute units for dynamic scaling
    cl_uint compute_units = 4;
    err = clGetDeviceInfo(device, CL_DEVICE_MAX_COMPUTE_UNITS, sizeof(cl_uint), &compute_units, NULL);
    if (err != CL_SUCCESS)
        compute_units = 4;

    // Dynamic thread count based on GPU capability
    size_t base_threads;
    if (compute_units >= 100)
    {
        base_threads = 4096;
    }
    else if (compute_units >= 50)
    {
        base_threads = 2048;
    }
    else if (compute_units >= 20)
    {
        base_threads = 1024;
    }
    else if (compute_units >= 10)
    {
        base_threads = compute_units * 8;
        if (base_threads < 32)
            base_threads = 32;
    }
    else
    {
        // Very old GPU (Fermi/Kepler) - use conservative settings
        base_threads = compute_units * 8;
        if (base_threads < 32)
            base_threads = 32;
    }

    const size_t MAX_THREADS = 8192;
    if (base_threads > MAX_THREADS)
        base_threads = MAX_THREADS;

    uint32_t seeds_per_thread = (uint32_t)((total_seeds + base_threads - 1) / base_threads);

    // Limit seeds per thread based on GPU age
    const uint32_t MAX_SEEDS_MODERN = 500000;
    const uint32_t MAX_SEEDS_OLD = 50000;
    const uint32_t MAX_SEEDS_ANCIENT = 5000;

    uint32_t max_seeds_per_thread;
    if (compute_units >= 20)
    {
        max_seeds_per_thread = MAX_SEEDS_MODERN;
    }
    else if (compute_units >= 10)
    {
        max_seeds_per_thread = MAX_SEEDS_OLD;
    }
    else
    {
        max_seeds_per_thread = MAX_SEEDS_ANCIENT;
    }

    if (seeds_per_thread > max_seeds_per_thread)
    {
        seeds_per_thread = max_seeds_per_thread;
    }

    size_t global_work_size = base_threads;

    // Create context and command queue
    context = clCreateContext(NULL, 1, &device, NULL, NULL, &err);
    CL_CHECK(err, "clCreateContext");

    queue = clCreateCommandQueue(context, device, CL_QUEUE_PROFILING_ENABLE, &err);
    CL_CHECK(err, "clCreateCommandQueue");

    // Load kernel source from file
    FILE *fp = fopen("crack_low32.cl", "r");
    if (!fp)
    {
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

    cl_mem r_base_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer r_base");

    cl_mem ox_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer ox");

    cl_mem oz_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer oz");

    cl_mem offset_range_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(uint32_t) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer offset_range");

    cl_mem spread_type_buffer = clCreateBuffer(context, CL_MEM_READ_ONLY, sizeof(int) * num_targets, NULL, &err);
    CL_CHECK(err, "clCreateBuffer spread_type");

    // Initialize result count to 0
    uint32_t zero = 0;
    err = clEnqueueWriteBuffer(queue, count_buffer, CL_TRUE, 0, sizeof(uint32_t), &zero, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer count init");

    // Write input data
    err = clEnqueueWriteBuffer(queue, r_base_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, r_base, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer r_base");

    err = clEnqueueWriteBuffer(queue, ox_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, ox, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer ox");

    err = clEnqueueWriteBuffer(queue, oz_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, oz, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer oz");

    err = clEnqueueWriteBuffer(queue, offset_range_buffer, CL_TRUE, 0, sizeof(uint32_t) * num_targets, offset_range, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer offset_range");

    err = clEnqueueWriteBuffer(queue, spread_type_buffer, CL_TRUE, 0, sizeof(int) * num_targets, spread_type, 0, NULL, NULL);
    CL_CHECK(err, "clEnqueueWriteBuffer spread_type");

    // Set kernel arguments
    err = clSetKernelArg(kernel, 0, sizeof(cl_mem), &results_buffer);
    err |= clSetKernelArg(kernel, 1, sizeof(cl_mem), &count_buffer);
    err |= clSetKernelArg(kernel, 2, sizeof(uint32_t), &start);
    err |= clSetKernelArg(kernel, 3, sizeof(uint32_t), &end);
    err |= clSetKernelArg(kernel, 4, sizeof(uint32_t), &seeds_per_thread);
    err |= clSetKernelArg(kernel, 5, sizeof(cl_mem), &r_base_buffer);
    err |= clSetKernelArg(kernel, 6, sizeof(cl_mem), &ox_buffer);
    err |= clSetKernelArg(kernel, 7, sizeof(cl_mem), &oz_buffer);
    err |= clSetKernelArg(kernel, 8, sizeof(cl_mem), &offset_range_buffer);
    err |= clSetKernelArg(kernel, 9, sizeof(cl_mem), &spread_type_buffer);
    err |= clSetKernelArg(kernel, 10, sizeof(uint32_t), &num_targets);
    err |= clSetKernelArg(kernel, 11, sizeof(uint32_t), &max_results);
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
    clReleaseMemObject(r_base_buffer);
    clReleaseMemObject(ox_buffer);
    clReleaseMemObject(oz_buffer);
    clReleaseMemObject(offset_range_buffer);
    clReleaseMemObject(spread_type_buffer);
    clReleaseKernel(kernel);
    clReleaseProgram(program);
    clReleaseCommandQueue(queue);
    clReleaseContext(context);
    free(kernel_source);

    return (int)result_count;
}