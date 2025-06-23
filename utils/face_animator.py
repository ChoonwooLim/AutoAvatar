import cv2
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw, ImageFont
import librosa
import soundfile as sf
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
import os
import tempfile
from typing import Tuple, List, Optional
import logging

class FaceAnimator:
    """얼굴 이미지를 사용하여 립싱크 비디오를 생성하는 클래스"""
    
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # 입술 랜드마크 인덱스 (MediaPipe Face Mesh)
        self.LIPS_LANDMARKS = [
            # 외부 입술
            61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318,
            # 내부 입술  
            78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415
        ]
        
        # 입 모양 변화를 위한 키포인트
        self.MOUTH_OPEN_LANDMARKS = [13, 14, 15, 16, 17, 18]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def detect_face_landmarks(self, image: np.ndarray) -> Optional[np.ndarray]:
        """얼굴에서 랜드마크를 검출합니다"""
        try:
            with self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            ) as face_mesh:
                
                # BGR을 RGB로 변환
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb_image)
                
                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0]
                    # 정규화된 좌표를 픽셀 좌표로 변환
                    h, w = image.shape[:2]
                    points = []
                    for landmark in landmarks.landmark:
                        x = int(landmark.x * w)
                        y = int(landmark.y * h)
                        points.append([x, y])
                    return np.array(points)
                    
        except Exception as e:
            self.logger.error(f"얼굴 랜드마크 검출 실패: {e}")
            
        return None
    
    def extract_audio_features(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """오디오에서 음성 특성을 추출합니다"""
        try:
            # 오디오 로드
            y, sr = librosa.load(audio_path, sr=22050)
            
            # 음성 강도 (RMS Energy)
            rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
            
            # MFCC 특성 (음성 특성)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # 스펙트럴 센트로이드 (음성의 밝기)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            
            # 시간 축 정보
            times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=512)
            
            # 입 열림 정도 계산 (RMS 에너지 기반)
            mouth_openness = np.interp(rms, (rms.min(), rms.max()), (0, 1))
            
            return mouth_openness, sr / 512  # 프레임 레이트 반환
            
        except Exception as e:
            self.logger.error(f"오디오 특성 추출 실패: {e}")
            return np.array([0]), 22050 / 512
    
    def animate_mouth(self, image: np.ndarray, landmarks: np.ndarray, 
                     mouth_openness: float) -> np.ndarray:
        """입 모양을 애니메이션합니다"""
        try:
            animated_image = image.copy()
            
            if landmarks is None:
                return animated_image
            
            # 입술 영역 추출
            lips_points = landmarks[self.LIPS_LANDMARKS]
            
            # 입 중심점 계산
            mouth_center = np.mean(lips_points, axis=0).astype(int)
            
            # 입 열림 정도에 따라 입술 모양 조정
            scale_factor = 1.0 + (mouth_openness * 0.3)  # 최대 30% 확장
            
            # 입술 영역을 중심으로 스케일링
            scaled_lips = []
            for point in lips_points:
                # 중심점으로부터의 벡터
                vector = point - mouth_center
                # 스케일링 적용 (세로 방향 더 많이)
                scaled_vector = vector * [1.0, scale_factor]
                scaled_point = mouth_center + scaled_vector.astype(int)
                scaled_lips.append(scaled_point)
            
            scaled_lips = np.array(scaled_lips)
            
            # 입술 영역 채우기 (자연스러운 색상)
            mask = np.zeros(animated_image.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [scaled_lips], 255)
            
            # 입술 색상 적용
            lip_color = [120, 80, 80]  # 자연스러운 입술 색상
            animated_image[mask > 0] = lip_color
            
            # 부드러운 블렌딩
            blurred_mask = cv2.GaussianBlur(mask, (5, 5), 0)
            for i in range(3):
                animated_image[:, :, i] = cv2.addWeighted(
                    image[:, :, i], 0.7,
                    animated_image[:, :, i], 0.3,
                    0
                )
            
            return animated_image
            
        except Exception as e:
            self.logger.error(f"입 애니메이션 실패: {e}")
            return image
    
    def create_lipsync_video(self, face_image_path: str, audio_path: str, 
                           output_path: str, fps: int = 30) -> bool:
        """얼굴 이미지와 오디오로 립싱크 비디오를 생성합니다"""
        try:
            self.logger.info("립싱크 비디오 생성 시작...")
            
            # 얼굴 이미지 로드
            face_image = cv2.imread(face_image_path)
            if face_image is None:
                raise ValueError("얼굴 이미지를 로드할 수 없습니다")
            
            # 이미지 크기 조정 (1080p 기준)
            target_height = 1080
            h, w = face_image.shape[:2]
            if h > target_height:
                scale = target_height / h
                new_w = int(w * scale)
                face_image = cv2.resize(face_image, (new_w, target_height))
            
            # 얼굴 랜드마크 검출
            landmarks = self.detect_face_landmarks(face_image)
            if landmarks is None:
                self.logger.warning("얼굴 랜드마크를 검출할 수 없어 정적 이미지로 처리합니다")
            
            # 오디오 특성 추출
            mouth_openness_array, audio_fps = self.extract_audio_features(audio_path)
            
            # 오디오 길이 계산
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            total_frames = int(duration * fps)
            
            # 임시 비디오 파일 생성
            temp_video_path = tempfile.mktemp(suffix='.mp4')
            
            # 비디오 라이터 설정
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(temp_video_path, fourcc, fps, 
                                         (face_image.shape[1], face_image.shape[0]))
            
            self.logger.info(f"총 {total_frames}프레임 생성 중...")
            
            # 각 프레임 생성
            for frame_idx in range(total_frames):
                # 현재 시간 계산
                current_time = frame_idx / fps
                
                # 오디오 특성에서 현재 시간의 입 열림 정도 계산
                audio_frame_idx = int(current_time * audio_fps)
                if audio_frame_idx < len(mouth_openness_array):
                    mouth_openness = mouth_openness_array[audio_frame_idx]
                else:
                    mouth_openness = 0
                
                # 입 애니메이션 적용
                if landmarks is not None:
                    animated_frame = self.animate_mouth(face_image, landmarks, mouth_openness)
                else:
                    # 랜드마크가 없으면 간단한 효과 적용
                    brightness = 1.0 + (mouth_openness * 0.1)
                    animated_frame = cv2.convertScaleAbs(face_image, alpha=brightness, beta=0)
                
                # 프레임 쓰기
                video_writer.write(animated_frame)
                
                # 진행상황 표시
                if frame_idx % (fps * 2) == 0:  # 2초마다
                    progress = (frame_idx / total_frames) * 100
                    self.logger.info(f"진행률: {progress:.1f}%")
            
            video_writer.release()
            
            # 오디오와 비디오 합성
            self.logger.info("오디오와 비디오 합성 중...")
            video_clip = VideoFileClip(temp_video_path)
            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            # 정리
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            os.unlink(temp_video_path)
            
            self.logger.info(f"립싱크 비디오 생성 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"립싱크 비디오 생성 실패: {e}")
            return False
    
    def create_talking_avatar(self, face_image_path: str, script_text: str,
                            audio_path: str, output_path: str,
                            background_color: Tuple[int, int, int] = (240, 240, 240),
                            add_subtitles: bool = True) -> bool:
        """완전한 말하는 아바타 비디오를 생성합니다"""
        try:
            self.logger.info("말하는 아바타 비디오 생성 시작...")
            
            # 먼저 립싱크 비디오 생성
            temp_lipsync_path = tempfile.mktemp(suffix='.mp4')
            if not self.create_lipsync_video(face_image_path, audio_path, temp_lipsync_path):
                return False
            
            # 비디오 클립 로드
            video_clip = VideoFileClip(temp_lipsync_path)
            
            # 배경 추가 (선택사항)
            if background_color:
                # 배경 크기를 비디오보다 크게 설정
                bg_width = int(video_clip.w * 1.2)
                bg_height = int(video_clip.h * 1.2)
                
                # 배경 이미지 생성
                bg_image = np.full((bg_height, bg_width, 3), background_color, dtype=np.uint8)
                bg_clip = ImageClip(bg_image, duration=video_clip.duration)
                
                # 비디오를 중앙에 배치
                video_clip = video_clip.set_position('center')
                final_clip = CompositeVideoClip([bg_clip, video_clip])
            else:
                final_clip = video_clip
            
            # 자막 추가 (선택사항) - ImageMagick 없이는 건너뛰기
            if add_subtitles and script_text:
                try:
                    from moviepy.editor import TextClip
                    
                    # 자막 설정
                    subtitle_clip = TextClip(script_text,
                                           fontsize=50,
                                           color='white',
                                           font='Arial-Bold',
                                           size=(final_clip.w * 0.8, None),
                                           method='caption').set_position(('center', 'bottom')).set_duration(final_clip.duration)
                    
                    # 자막 배경 추가
                    subtitle_bg = TextClip(script_text,
                                         fontsize=50,
                                         color='black',
                                         font='Arial-Bold',
                                         size=(final_clip.w * 0.8, None),
                                         method='caption').set_position(('center', 'bottom')).set_duration(final_clip.duration)
                    
                    # 합성
                    final_clip = CompositeVideoClip([final_clip, subtitle_bg.set_position(('center', final_clip.h * 0.85)), 
                                                   subtitle_clip.set_position(('center', final_clip.h * 0.85))])
                except Exception as e:
                    self.logger.warning(f"자막 추가 실패 (ImageMagick 필요): {e}")
                    self.logger.info("자막 없이 비디오를 생성합니다...")
            
            # 최종 비디오 저장
            final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
            
            # 정리
            video_clip.close()
            final_clip.close()
            os.unlink(temp_lipsync_path)
            
            self.logger.info(f"말하는 아바타 비디오 생성 완료: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"말하는 아바타 비디오 생성 실패: {e}")
            return False 