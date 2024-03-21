/**
 *   #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *  %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *  %    %## #    CC        V    V  MM M  M MM RR    RR
 *   ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *   (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *     #%    %*    CCCCCC     VV    MM      MM RR    RR
 *    .%    %/
 *       (%.      Computer Vision & Mixed Reality Group
 *                For more information see <http://cvmr.info>
 *
 * This file is part of RBOT.
 *
 *  @copyright:   RheinMain University of Applied Sciences
 *                Wiesbaden Rüsselsheim
 *                Germany
 *     @author:   Henning Tjaden
 *                <henning dot tjaden at gmail dot com>
 *    @version:   1.0
 *       @date:   30.08.2018
 *
 * RBOT is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * RBOT is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with RBOT. If not, see <http://www.gnu.org/licenses/>.
 */

#include <fstream>
#include <QApplication>
#include <QThread>
#include <QDir>
#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>

#include "object3d.h"
#include "pose_estimator6d.h"

using namespace std;
using namespace cv;

#define NUM_FRAMES_PER_CONFIG 1000
#define NUM_DIGITS_PER_FRAME_FILENAME 4
// On RBOT dataset, no camera distortion parameters are given, so might as well
// leave this as false.
#define SHOULD_UNDISTORT_FRAME false

float TRANS_ERROR_THRESH = 1000 * 0.05f;
float ROT_ERROR_THRESH = 5.0f * CV_PI / 180.0f;


struct EvalConfig {
    std::string bodName;
    std::string seqName;
    bool modelOcclusions;
};


bool SHOW_RESULTS = false;
std::vector<cv::Matx44f> gtPosesMain;
std::vector<cv::Matx44f> gtPosesOccluding;

QDir datasetDir("D:\\Datasets\\RBOT_dataset\\RBOT_dataset");

cv::Mat drawResultOverlay(const vector<Object3D*>& objects, const cv::Mat& frame)
{
    // render the models with phong shading
    RenderingEngine::Instance()->setLevel(0);
    
    vector<Point3f> colors;
    colors.push_back(Point3f(1.0, 0.5, 0.0));
    //colors.push_back(Point3f(0.2, 0.3, 1.0));
    RenderingEngine::Instance()->renderShaded(vector<Model*>(objects.begin(), objects.end()), GL_FILL, colors, true);

    // download the rendering to the CPU
    Mat rendering = RenderingEngine::Instance()->downloadFrame(RenderingEngine::RGB);
    
    // download the depth buffer to the CPU
    Mat depth = RenderingEngine::Instance()->downloadFrame(RenderingEngine::DEPTH);
    
    // compose the rendering with the current camera image for demo purposes (can be done more efficiently directly in OpenGL)
    Mat result = frame.clone();
    for(int y = 0; y < frame.rows; y++)
    {
        for(int x = 0; x < frame.cols; x++)
        {
            Vec3b color = rendering.at<Vec3b>(y,x);
            if(depth.at<float>(y,x) != 0.0f)
            {
                result.at<Vec3b>(y,x)[0] = color[2];
                result.at<Vec3b>(y,x)[1] = color[1];
                result.at<Vec3b>(y,x)[2] = color[0];
            }
        }
    }
    return result;
}



void ReadPosesFromFile( const QString &path, std::vector<cv::Matx44f>& poses) {
    std::ifstream ifs(path.toStdString());
    if (!ifs.is_open() || ifs.fail()) {
        ifs.close();
        std::cerr << "Problem opening file " << path.toStdString() << std::endl;
    }

    poses.resize(NUM_FRAMES_PER_CONFIG + 1);
    std::string line;
    std::getline(ifs, line); // First line is just "headers".
    for (auto &pose : poses) {
        std::getline(ifs, line);
        std::istringstream iss(line);

        // First, the rotation values are put into the matrix.
        for (int i = 0; i < 3; ++i) {
            for (int j = 0; j < 3; ++j) {
                iss >> pose(i, j);
            }
        }
        // Then come the translation column entries.
        for (int i = 0; i < 3; ++i) {
            iss >> pose(i, 3);
        }

        // Bottom-right entry of matrix.
        pose(3, 3) = 1.f;
    }
}

// Check that translation and rotation errors are below threshold.
// Errors are calculated as discussed in RBOT 2018 paper.
bool MeasureSuccess(const cv::Matx44f &poseResult, const cv::Matx44f &poseGT) {
    float trace = cv::sum(
        (poseResult.get_minor<3,3>(0,0).t() * poseGT.get_minor<3,3>(0,0)).diag()
    )[0];

    float rotError = acos((trace - 1.0f) / 2.0f);

    float transError = cv::norm(poseResult.col(3) - poseGT.col(3), cv::NORM_L2);

    return (transError <= TRANS_ERROR_THRESH && rotError <= ROT_ERROR_THRESH);
}

// Prepends zeros to frame number strings.
// I.e., turns "1" into "0001", etc.
std::string FrameLongNum(int frameNum)
{
    std::string retStr = std::to_string(frameNum);
    for (int i = retStr.length(); i < NUM_DIGITS_PER_FRAME_FILENAME; ++i)
        retStr = "0" + retStr;
    return retStr;
}

// Evaluate a single object for a single type of scene.
float EvalSingleConfig(const EvalConfig& run_configuration)
{
    // camera image size
    int width = 640;
    int height = 512;

    // near and far plane of the OpenGL view frustum
    float zNear = 10.0;
    float zFar = 10000.0;

    // camera instrinsics
    Matx33f K = Matx33f(650.048, 0, 324.328, 0, 647.183, 257.323, 0, 0, 1);
    Matx14f distCoeffs =  Matx14f(0.0, 0.0, 0.0, 0.0);

    // distances for the pose detection template generation
    vector<float> distances = {200.0f, 400.0f, 600.0f};

    // load 3D objects
    vector<Object3D*> objects;

    QString bodStrQt = QString::fromStdString(run_configuration.bodName);
    QString seqStrQt = QString::fromStdString(run_configuration.seqName);

    QString localObjPath = bodStrQt + "/" + bodStrQt + ".obj";

    std::string objPath = datasetDir.filePath(localObjPath).toStdString();

    objects.push_back(new Object3D(objPath, 15, -35, 515, 55, -20, 205, 1.0, 0.55f, distances));
    //objects.push_back(new Object3D("data/a_second_model.obj", -50, 0, 600, 30, 0, 180, 1.0, 0.55f, distances2));

    objects[0]->setPose(gtPosesMain[0]);
    objects[0]->setInitialPose(gtPosesMain[0]);

    if (run_configuration.modelOcclusions)
    {
        std::string squirrelPath = datasetDir.filePath("squirrel_small.obj").toStdString();

        objects.push_back(new Object3D(squirrelPath, 15, -35, 515, 55, -20, 205, 1.0, 0.55f, distances));

        objects[1]->setPose(gtPosesOccluding[0]);
        objects[1]->setInitialPose(gtPosesOccluding[0]);
    }
    
    // create the pose estimator
    PoseEstimator6D* poseEstimator = new PoseEstimator6D(width, height, zNear, zFar, K, distCoeffs, objects);
    
    // move the OpenGL context for offscreen rendering to the current thread, if run in a seperate QT worker thread (unnessary in this example)
    //RenderingEngine::Instance()->getContext()->moveToThread(this);
    
    // active the OpenGL context for the offscreen rendering engine during pose estimation
    RenderingEngine::Instance()->makeCurrent();


    // This is the common part of all frame filepaths for this config, though
    // the frame number has not yet been appended.
    std::string configFramesLoc = datasetDir.filePath(bodStrQt + "/frames/" + seqStrQt).toStdString();

    Mat frame = imread(configFramesLoc + FrameLongNum(0) + ".png");

    poseEstimator->toggleTracking(frame, 0, SHOULD_UNDISTORT_FRAME);
    if (run_configuration.modelOcclusions)
        poseEstimator->toggleTracking(frame, 1, SHOULD_UNDISTORT_FRAME);

    float totalSuccesses = 0.f;

    for (int i = 0; i < NUM_FRAMES_PER_CONFIG; ++i)
    {
        // obtain an input image
        frame = imread(configFramesLoc + FrameLongNum(i + 1) + ".png");

        // the main pose update call
        poseEstimator->estimatePoses(frame, SHOULD_UNDISTORT_FRAME, false);

        bool success = MeasureSuccess(objects[0]->getPose(), gtPosesMain[i + 1]);

        float successFloat = success ? 1.f : 0.f;
        totalSuccesses += successFloat;
        if (!success)
        {
            // Toggle tracking off
            poseEstimator->toggleTracking(frame, 0, SHOULD_UNDISTORT_FRAME); 
            // Reset pose to current GT
            objects[0]->setPose(gtPosesMain[i + 1]);
            // Reset pose to current GT
            objects[0]->setInitialPose(gtPosesMain[i + 1]); 
            // Toggle tracking back on, make histograms
            poseEstimator->toggleTracking(frame, 0, SHOULD_UNDISTORT_FRAME); 
        }

        // Calculate results for occluding body
        if (run_configuration.modelOcclusions) {
            if (!MeasureSuccess(objects[1]->getPose(), gtPosesOccluding[i + 1]))
            {
            // Toggle tracking off
            poseEstimator->toggleTracking(frame, 1, SHOULD_UNDISTORT_FRAME); 
            // Reset pose to current GT
            objects[1]->setPose(gtPosesOccluding[i + 1]);
            // Reset pose to current GT
            objects[1]->setInitialPose(gtPosesOccluding[i + 1]); 
            // Toggle tracking back on, make histograms
            poseEstimator->toggleTracking(frame, 1, SHOULD_UNDISTORT_FRAME);            }
        }
        
        if(SHOW_RESULTS)
        {
            // render the models with the resulting pose estimates ontop of the input image
            Mat result = drawResultOverlay(objects, frame);

            imshow("result", result);

            int key = waitKey(1);

            if(key == (int)'c')
                break;
        }
    }
    
    // deactivate the offscreen rendering OpenGL context
    RenderingEngine::Instance()->doneCurrent();
    
    // clean up
    RenderingEngine::Instance()->destroy();
    
    for(int i = 0; i < objects.size(); i++)
    {
        delete objects[i];
    }
    objects.clear();
    
    delete poseEstimator;

    return totalSuccesses / NUM_FRAMES_PER_CONFIG;
}

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);



    ReadPosesFromFile(datasetDir.filePath("poses_first.txt"), gtPosesMain);

    ReadPosesFromFile(datasetDir.filePath("poses_second.txt"), gtPosesOccluding);

    // Most of the models, including the squirrel used for modelled occlusions,
    // use too much RAM for their histograms for my computer to handle well.
    // So I'm just going to test a subset and leave the full set here but
    // commented out.

    std::vector<std::string> bodyNames
    {
        "bakingsoda", "broccolisoup", "clown", "cube", "koalacandy"
    };

    std::vector<std::string> sequenceNames
    {
         "a_regular", "b_dynamiclight", "c_noisy", "d_occlusion"
    };

    std::vector<bool> occlusionBools{false, false, false, false};

    // std::vector<std::string> bodyNames
    // {
    //     "ape", "bakingsoda", "benchviseblue", "broccolisoup", "cam", "can",
    //     "cat", "clown", "cube", "driller", "duck", "eggbox", "glue", "iron",
    //     "koalacandy", "lamp", "phone", "squirrel"
    // };
    // std::vector<std::string> sequenceNames
    // {
    //     "a_regular", "b_dynamiclight", "c_noisy", "d_occlusion", "d_occlusion"
    // };
    // std::vector<bool> occlusionBools{false, false, false, false, true};

    std::vector<EvalConfig> evalConfigs;

    for (size_t i = 0; i < sequenceNames.size(); ++i) {
        for (const auto& bodyName: bodyNames) {
            evalConfigs.push_back(EvalConfig{
                bodyName, sequenceNames[i], occlusionBools[i]
            });
        }
    }

    for (int i = 0; i < int(evalConfigs.size()); ++i) {
        float avgSuccess = EvalSingleConfig(evalConfigs[i]);
        std::string modString = evalConfigs[i].modelOcclusions ? " (modeled)" : "";
        std::cout << evalConfigs[i].seqName << modString << " - "
            << evalConfigs[i].bodName << ": " << avgSuccess << std::endl;
    }


    return 0;
}
