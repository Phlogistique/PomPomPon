#include <cassert>
#include <cmath>
#include <iostream>
#include <opencv/cv.h>
#include <opencv/highgui.h>

#define WINDOW(name)		"PomPom - " name

#define PROCESSING_WINDOW	WINDOW("Traitement")
#define INPUT_WINDOW		WINDOW("Input")
#define INTERSECT_WINDOW	WINDOW("Intersect")

#define SMOOTH_PARAM		"Aperture du flou"

#define APERTURE (1+aperture*2)

#define IMG_SZ cvSize(320, 240)
using namespace std;
using namespace cv;

int hue_target = 127;
int hue_tolerance = 10;
int sat_target = 127;
int sat_tolerance = 10;
int val_target = 127;
int val_tolerance = 10;
int dilate_iter = 3;
IplImage *resize_frame;
IplImage *smooth_frame;

void on_mouse(int event, int x, int y, int flags, void* param)
{
	if (event != CV_EVENT_LBUTTONUP)
		return;

	cout << "Clicked (" << x << "," << y << ")" << endl;

	uchar *pixel = &((uchar*)(smooth_frame->imageData +
				smooth_frame->widthStep*y))[x*3];

	hue_target = pixel[0];
	sat_target = pixel[1];
	val_target = pixel[2];
	cout	<< "hue="  << hue_target
		<< " sat=" << sat_target
		<< " val=" << val_target << endl;
}

int clamp(int x, int min, int max) {
	if (x < min) return min;
	if (x > max) return max;
	return x;
}

int main(int argc, char *const argv[])
{
	int aperture = 1;
	//int contour_bs = 20;

	cvNamedWindow(INPUT_WINDOW, CV_WINDOW_AUTOSIZE);
	cvNamedWindow(PROCESSING_WINDOW, CV_WINDOW_AUTOSIZE);
	cvNamedWindow(INTERSECT_WINDOW, CV_WINDOW_AUTOSIZE);

	cvSetMouseCallback(INPUT_WINDOW, on_mouse);

	cvCreateTrackbar(SMOOTH_PARAM, PROCESSING_WINDOW,
			&aperture, 10, NULL);
	cvCreateTrackbar("Hue tolerance", PROCESSING_WINDOW, &hue_tolerance, 127, NULL);
	cvCreateTrackbar("Sat tolerance", PROCESSING_WINDOW, &sat_tolerance, 127, NULL);
	cvCreateTrackbar("Val tolerance", PROCESSING_WINDOW, &val_tolerance, 127, NULL);
	cvCreateTrackbar("Dilatation", PROCESSING_WINDOW, &dilate_iter, 20, NULL);

	CvCapture *camera = cvCreateCameraCapture(CV_CAP_ANY);

	IplImage *camera_frame = cvQueryFrame(camera);

	if (NULL == camera_frame) {
		cerr << "No webcam, exiting." << endl;
		exit(1);
	}

	resize_frame = cvCreateImage(IMG_SZ, IPL_DEPTH_8U, 3);
	IplImage *hsv_frame = cvCreateImage(IMG_SZ, IPL_DEPTH_8U, 3);
	smooth_frame = cvCreateImage(IMG_SZ, IPL_DEPTH_8U, 3);

	IplImage *bin_frame = cvCreateImage(IMG_SZ, IPL_DEPTH_8U, 1);
	IplImage *mask = cvCreateImage(IMG_SZ, IPL_DEPTH_8U, 1);

	// Boucle de traitements
	while (NULL != (camera_frame = cvQueryFrame(camera))) {

		cvResize(camera_frame, resize_frame, CV_INTER_NN);
		cvCvtColor(resize_frame, hsv_frame, CV_RGB2HSV);
		cvSmooth(hsv_frame, smooth_frame, CV_MEDIAN, APERTURE);
		//cvSplit(smooth_frame, hue, sat, val, NULL);
		
		CvScalar lower = cvScalar(
				clamp(hue_target - hue_tolerance, 0, 0xFF),
				clamp(sat_target - sat_tolerance, 0, 0xFF),
				clamp(val_target - val_tolerance, 0, 0xFF));
		CvScalar upper = cvScalar(
				clamp(hue_target + hue_tolerance, 0, 0xFF),
				clamp(sat_target + sat_tolerance, 0, 0xFF),
				clamp(val_target + val_tolerance, 0, 0xFF));

		cvInRangeS(smooth_frame, lower, upper, bin_frame);

		cvDilate(bin_frame, mask, NULL, dilate_iter);
#if 0
		cvDilate(bin_frame, eroded_frame, NULL, ITERATION);

		// Look for contours
		CvSeq *contour = 0;
		CvMemStorage *storage = cvCreateMemStorage();
		cvFindContours(eroded_frame, storage, &contour,
				sizeof(CvContour), CV_RETR_EXTERNAL,
				CV_CHAIN_APPROX_SIMPLE);

		for (; contour != 0; contour = contour->h_next) {
			CvRect boundingRect = cvBoundingRect(contour, 0);


			if (boundingRect.width > contour_bs &&
			    boundingRect.height > contour_bs)
				cvRectangle(dst_frame,
					(CvPoint) {
						boundingRect.x,
						boundingRect.y,
					},
					(CvPoint) {
						boundingRect.x +
						boundingRect.width,
						boundingRect.y +
						boundingRect.height,
					},
					CV_RGB(255,0,0), // color
					3); // thickness
		}
#endif

		// Affichage des images
		cvShowImage(INPUT_WINDOW, resize_frame);
		cvShowImage(INTERSECT_WINDOW, mask);

		// Image suivante ou arrêt
		int key = cvWaitKey(40);
		if (key == 'q' || key == 'Q')
			break;
		if (key == 32)
			cvWaitKey(10000);

	}

	return 0;
}
