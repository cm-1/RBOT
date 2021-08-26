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
#include "AugRealityFilter.h"
#include <QDebug>
#include <QGuiApplication>
#include <QScreen>

#include <QOpenGLContext>
#include <QOpenGLFunctions>

#include <opencv2/imgproc.hpp>

struct RGBA {
    uchar blue;
    uchar green;
    uchar red;
    uchar alpha;
};

// -----------------------------------------------------------------------------
// CLASS: AugRealityFilter
// -----------------------------------------------------------------------------
AugRealityFilter::AugRealityFilter( QObject* parent )
    : QAbstractVideoFilter( parent )
{
    qDebug() << "New Filter Created!";
    m_Runnable = nullptr;
    m_trackingStatus = false;
    m_currentFramerateText = "FPS";
}

QVideoFilterRunnable* AugRealityFilter::createFilterRunnable()
{
    m_Runnable = new AugRealityFilterRunnable( this );
    return m_Runnable;
}

bool AugRealityFilter::getTrackingStatus() const
{
    return m_trackingStatus;
}

void AugRealityFilter::setTrackingStatus(const bool &updatedTrackingStatus)
{
    if (updatedTrackingStatus != m_trackingStatus) {
        m_trackingStatus = updatedTrackingStatus;
        emit trackingStatusChanged();
    }
}

QString AugRealityFilter::getFramerateText() const
{
    return m_currentFramerateText;
}

void AugRealityFilter::setFramerateText(const QString &updatedFramerateText)
{
    if (updatedFramerateText != m_currentFramerateText) {
        m_currentFramerateText = updatedFramerateText;
        emit framerateTextChanged();
    }
}


// -----------------------------------------------------------------------------
// CLASS: AugRealityFilterRunnable
// -----------------------------------------------------------------------------
AugRealityFilterRunnable::AugRealityFilterRunnable( AugRealityFilter* filter ) :
    m_Filter( filter )
{
qDebug() << "New Runnable Created!";

    frameStartedCounter = 0;
    frameEndedCounter = 0;
}

cv::Mat AugRealityFilterRunnable::matFromVideoFrame(QVideoFrame *input) {

    cv::Mat mat;



    // Construct an OpenCV Mat that points at this memory.
    cv::Mat* matMapped;
    
    if (input->isMapped()) {
        matMapped = new cv::Mat(input->height(),input->width(), CV_8UC4, input->bits());
        // Create a copy, so that we have a Mat separate from the original memory.
        mat = matMapped->clone();

        // Vertical flip
        cv::flip(mat, mat, 0); // Third param of "0" => vertical flip

        // Now that we have our copy, we can release the mapped frame.
        matMapped->release();
    }
    else {
        mat = cv::Mat::zeros(input->height(), input->width(), CV_8UC4);
    }

    return mat;
}

QVideoFrame AugRealityFilterRunnable::run( QVideoFrame *input, const QVideoSurfaceFormat &surfaceFormat, RunFlags flags )
{
    Q_UNUSED( flags ) // flags unused at this time.
    Q_UNUSED( surfaceFormat ) // Also unused at this time.

    if (!input || !input->isValid()) {
        qDebug() << "===== PROBLEM WITH INPUT FRAME! ABORTING FILTER FOR THIS FRAME! =====";
        return *input;
    }

    // Something to tell us whether filtering failed mid-frame.
    if (frameStartedCounter != frameEndedCounter) {
        frameEndedCounter = frameStartedCounter; // Update counters to "fix"."
        qDebug() << "=== Mismatch for frame: " << frameStartedCounter << " ===";
    }
    frameStartedCounter++;

    // The clone mat is currently unneeded, but will be required in a very near commit.
    input->map(QAbstractVideoBuffer::ReadWrite);
    // cv::Mat mat = matFromVideoFrame(input);
    
    cv::Mat* matToDisplay;

    // On PC, we directly edit a mat that has *input's mapped data in it.
    matToDisplay = new cv::Mat(input->height(),input->width(), CV_8UC4, input->bits());


    
    // For now, we just test by outputting the frame number.
    std::stringstream infoStream;
    infoStream << "Frame: " << frameStartedCounter << "\n";
    QString qResult = QString::fromStdString(infoStream.str());
    m_Filter->setFramerateText(qResult);


    cv::Point3f GREEN = cv::Point3f(0, 255, 0);
    float overlayAlpha = 0.5f;
    drawResultOverlay(matToDisplay, GREEN, overlayAlpha);

    // Release the memory pointed to by our non-clone OpenCV mat
    matToDisplay->release(); 
    
    input->unmap();
    frameEndedCounter++;
    return *input; // Return the modified frame.
}

void AugRealityFilterRunnable::drawResultOverlay(cv::Mat* frame, cv::Point3f color, float alpha)
{
    for(int y = 0; y < frame->rows; y++)
    {
        for(int x = 0; x < frame->cols; x++)
        {
            if(x < frameStartedCounter % 200 && y < frameStartedCounter % 200)
            {
                cv::Vec4b overlayColor(color.x, color.y, color.z, 1.0f);

                float beta = 1.0f - alpha;
                RGBA& rgba = frame->ptr<RGBA>(y)[x];
                rgba.red = alpha*rgba.red + beta*overlayColor[0];
                rgba.green = alpha*rgba.green + beta*overlayColor[1];
                rgba.blue = alpha*rgba.blue + beta*overlayColor[2];
                rgba.alpha = 1.0f;
            }
        }
    }
}
