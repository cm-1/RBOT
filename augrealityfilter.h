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
#ifndef __AugRealityVideoFilter__
#define __AugRealityVideoFilter__

#include <QAbstractVideoFilter>
#include <QVideoFilterRunnable>

#include <opencv2/core.hpp>


class AugRealityFilterRunnable; // So that we can ref the runnable in the filter

class AugRealityFilter : public QAbstractVideoFilter
{
    Q_OBJECT

    // Allows shared knowledge of video orientation between QML and C++.
    // I don't really use it, but it may be important for some use cases.
    Q_PROPERTY( int videoOutputOrientation MEMBER m_VideoOutputOrientation )

    // I do use tracking status, though. So this should also be shared.
    Q_PROPERTY( bool trackingStatus READ getTrackingStatus WRITE setTrackingStatus NOTIFY trackingStatusChanged)

    // This lets us set the fps text in main.qml from the C++ code.
    Q_PROPERTY( QString framerateText READ getFramerateText WRITE setFramerateText NOTIFY framerateTextChanged)

public:
    AugRealityFilter( QObject* parent = nullptr );
    QVideoFilterRunnable* createFilterRunnable();

    // These are for communication with the QML.
    bool getTrackingStatus() const;
    void setTrackingStatus(const bool &updatedTrackingStatus);
    QString getFramerateText() const;
    void setFramerateText(const QString &updatedFramerateText);

    int m_VideoOutputOrientation;

signals:
    // Again, stuff to signal changes to the QML.
    void trackingStatusChanged();
    void framerateTextChanged();

private:
    // Reference to the runnable. This lets us change its state based on
    // button presses and whatnot from the QML. This might not feature
    // in this public branch, but it's super important for many use cases.
    AugRealityFilterRunnable* m_Runnable;

    bool m_trackingStatus;
    QString m_currentFramerateText;
};

class AugRealityFilterRunnable : public QVideoFilterRunnable
{
public:
    AugRealityFilterRunnable( AugRealityFilter* filter );
    QVideoFrame run( QVideoFrame *input, const QVideoSurfaceFormat &surfaceFormat, RunFlags flags );

protected:
    AugRealityFilter* m_Filter;

private:
    /**
     *  Converts a QVideoFrame into an OpenCV Matrix.
     *  NOTE: DOES NOT WORK FOR CERTAIN CAMERAS! I still need to add in a
     *  check/conversion for YUV, for example.
     *  NOTE: ASSUMES INPUT HAS ALREADY BEEN MAPPED!
     *
     *  @param input  The QVideoFrame input for this frame for the filter.
     *  @return An OpenCV matrix with the same contents as the input frame.
     */
    cv::Mat matFromVideoFrame(QVideoFrame * input);

    /**
     *  Superimposes our renders and our input video frame for a final output.
     *
     *  @param frame  The QVideoFrame input for this frame for the filter.
     *  @param color  The colour to use for the overlay.
     *  @param alpha  The alpha/transparency to use for the overlay.
     */
    void drawResultOverlay(cv::Mat* frame, cv::Point3f color, float alpha);


    int frameStartedCounter;
    int frameEndedCounter;
};

#endif