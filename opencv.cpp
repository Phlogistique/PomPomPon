#include <cassert>
#include <cmath>
#include <iostream>
#include <opencv/cv.h>
#include <opencv/highgui.h>

#define OUTPUT_WINDOW "Output"
#define PROCESSING_WINDOW "Traitement"
#define THRESHOLD_BS_TRACKBAR "Taille blocs seuillage"
#define THRESHOLD_PARAM "Paramètre du seuillage"
#define SMOOTH_PARAM "Aperture du flou"
#define MORPH_ITER "Itérations dilatation"
#define BOUNDING_BS "Taille des formes"

#define BLOCKSIZE (5+blocksize*2)
#define APERTURE (1+aperture*2)
#define ITERATION (1+iteration)

using namespace std;

#define CONTOUR_DURATION 30

static void update(list<ContourMem> &l, CvRect &rect, int &now) {
	bool found = false;
	for (auto i = l.begin(); i != l.end(); i++)
		if (i->dead(now)) {
			l.
		}
		if (i->update(rect, now))
			found = true;

	if (!found) {
		ContourMem *contourMem = new ContourMem(rect, now);
		l.push_start(*contourMem);
	}
}

class ContourMem {
	public:
	ContourMem(CvRect &rect, int &now) :
		rect(rect),
		last_seen(now),
		dead(false),
		color(next_color())
	{
	}

	bool same(CvRect& other) {
		long xoff, yoff;
		xoff = abs(center().x - center_(other).x);
		yoff = abs(center().y - center_(other).y);

		return xoff < rect->width / 2 && yoff < rect->height / 2;
	}

	bool dead(int &now) {
		return now - last_seen > CONTOUR_DURATION;
	}

	/* Returns true if this is the same rectangle, false otherwise */
	bool update(CvRect &other, int &now) {
		if (last_seen == now || !same(other)) return false;

		rect = other;
		last_seen = now;

		return true;
	}

	CvPoint center() { return center_(rect); }
	CvScalar color;

	private:

	static CvScalar next_color() {
		static int i;
		if (++i > sizeof colors / sizeof colors[0])
			i = 0;
		return colors[i];
	}

	static CvScalar colors[] = {
		CV_RGB(255,0,0);
		CV_RGB(0,255,0);
		CV_RGB(0,0,255);
		CV_RGB(0,255,255);
		CV_RGB(255,0,255);
		CV_RGB(255,255,0);
	};

	CvPoint center_(CvRect &r) {
		return (CvPoint) {
			r.x + r.width / 2,
			r.y + r.height/ 2,
		};
	}
	int last_seen;
	bool dead;
	CvRect rect;
}

// Point d'entrée du programme
int main(int argc, char *const argv[])
{
	int frame_number = 0;
	int thresh = 90;
	int blocksize = 0;
	int aperture = 1;
	int iteration = 0;
	int threshold_param1 = 5;
	int contour_bs = 20;
	list<ContourMem> remembered;

	cvNamedWindow(OUTPUT_WINDOW, CV_WINDOW_AUTOSIZE);
	cvNamedWindow(PROCESSING_WINDOW, CV_WINDOW_AUTOSIZE);

	cvCreateTrackbar(THRESHOLD_BS_TRACKBAR, PROCESSING_WINDOW,
			&blocksize, 10, NULL);
	cvCreateTrackbar(THRESHOLD_PARAM, PROCESSING_WINDOW,
			&threshold_param1, 20, NULL);
	cvCreateTrackbar(SMOOTH_PARAM, PROCESSING_WINDOW,
			&aperture, 10, NULL);
	cvCreateTrackbar(MORPH_ITER, PROCESSING_WINDOW,
			&iteration, 10, NULL);
	cvCreateTrackbar(BOUNDING_BS, PROCESSING_WINDOW,
			&contour_bs, 100, NULL);

	cvNamedWindow("Input", CV_WINDOW_AUTOSIZE);

	CvPoint2D32f *src = new CvPoint2D32f[4];
       	src[0] = cvPoint2D32f(45,70);
	src[1] = cvPoint2D32f(480,125);
	src[2] = cvPoint2D32f(620,360);
	src[3] = cvPoint2D32f(60,410);

	CvPoint2D32f *dst = new CvPoint2D32f[4];
	dst[0] = cvPoint2D32f(0,0);
	dst[1] = cvPoint2D32f(640,0);
	dst[2] = cvPoint2D32f(640,480);
	dst[3] = cvPoint2D32f(0,480);
	
	CvMat *mapMatrix = cvCreateMat(3, 3, CV_32FC1);

	cvGetPerspectiveTransform(src, dst, mapMatrix);

	// Camera
	//CvCapture *camera = cvCreateCameraCapture(CV_CAP_ANY);
	CvCapture *camera = cvCaptureFromAVI("video.avi");

	// Images
	IplImage *camera_frame = cvQueryFrame(camera);
	IplImage *resize_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 3);
	IplImage *gray_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 1);
	IplImage *bin_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 1);
	IplImage *median_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 1);
	IplImage *eroded_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 1);
	IplImage *warped_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 1);
	IplImage *dst_frame =
	    cvCreateImage(cvSize(640, 480), IPL_DEPTH_8U, 3);

	// Boucle de traitements
	while (camera_frame = cvQueryFrame(camera)) {

		// Taille
		cvResize(camera_frame, resize_frame, CV_INTER_NN);
		
		cvCvtColor(resize_frame, gray_frame, CV_RGB2GRAY);

		cvSmooth(gray_frame, median_frame, CV_MEDIAN, APERTURE);

		cvWarpPerspective(median_frame, warped_frame, mapMatrix);

		cvAdaptiveThreshold(warped_frame, bin_frame, 255,
				CV_ADAPTIVE_THRESH_GAUSSIAN_C,
				CV_THRESH_BINARY_INV, BLOCKSIZE, 9);

		cvDilate(bin_frame, eroded_frame, NULL, ITERATION);

		cvCvtColor(eroded_frame, dst_frame, CV_GRAY2RGB);
		
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

		// Affichage des images
		cvShowImage("Input", resize_frame);
		cvShowImage("Output", dst_frame);

		// Image suivante ou arrêt
		int key = cvWaitKey(40);
		if (key == 'q' || key == 'Q')
			break;
		if (key == 32)
			cvWaitKey(10000);

		frame_number++;
	}

	return 0;
}
