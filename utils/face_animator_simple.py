import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import librosa
import soundfile as sf
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
import os
import tempfile
from typing import Tuple, List, Optional
import logging

class SimpleFaceAnimator:
    """자막 없이 립싱크만 수행하는 간단한 얼굴 애니메이터"""
    
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
            
            # 음성 강도 (RMS Energy) - 더 세밀한 분석
            hop_length = 256  # 더 세밀한 시간 해상도
            rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=hop_length)[0]
            
            # 스펙트럴 센트로이드 (음성의 밝기)
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
            
            # 제로 크로싱 레이트 (음성 활동 감지)
            zcr = librosa.feature.zero_crossing_rate(y, frame_length=1024, hop_length=hop_length)[0]
            
            # 복합적인 입 열림 정도 계산
            # RMS 에너지를 기본으로 하되, 스펙트럴 특성도 고려
            normalized_rms = np.interp(rms, (rms.min(), rms.max()), (0, 1))
            normalized_centroid = np.interp(spectral_centroids, 
                                          (spectral_centroids.min(), spectral_centroids.max()), 
                                          (0, 0.3))  # 센트로이드는 보조적으로만 사용
            
            # 최종 입 열림 정도 (RMS 80% + 센트로이드 20%)
            mouth_openness = normalized_rms * 0.8 + normalized_centroid * 0.2
            
            # 스무딩 적용 (급격한 변화 방지)
            from scipy import ndimage
            mouth_openness = ndimage.gaussian_filter1d(mouth_openness, sigma=1.0)
            
            # 최소/최대값 조정 (너무 미세한 변화 방지)
            mouth_openness = np.clip(mouth_openness, 0.1, 0.9)
            
            return mouth_openness, sr / hop_length  # 프레임 레이트 반환
            
        except Exception as e:
            self.logger.error(f"오디오 특성 추출 실패: {e}")
            # 기본 더미 데이터
            duration = 1.0
            try:
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                audio_clip.close()
            except:
                pass
            
            # 기본 패턴 생성 (약간의 랜덤 변화)
            frames = int(duration * 22050 / 256)
            dummy_pattern = np.random.uniform(0.2, 0.6, frames)
            return dummy_pattern, 22050 / 256
    
    def animate_mouth(self, image: np.ndarray, landmarks: np.ndarray, 
                     mouth_openness: float) -> np.ndarray:
        """입 모양을 애니메이션합니다"""
        try:
            animated_image = image.copy()
            
            if landmarks is None:
                # 랜드마크가 없으면 밝기 변화로 대체
                brightness = 1.0 + (mouth_openness * 0.15)
                return cv2.convertScaleAbs(animated_image, alpha=brightness, beta=5)
            
            # 입술 영역 추출 (더 정확한 인덱스 사용)
            upper_lip = [61, 84, 17, 314, 405, 320, 307, 375, 321, 308, 324, 318]
            lower_lip = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415]
            
            # 입 열림 정도에 따른 변형 강도 증가
            mouth_scale = 1.0 + (mouth_openness * 0.8)  # 최대 80% 확장
            
            # 상하 입술 분리해서 처리
            if len(landmarks) > max(upper_lip + lower_lip):
                upper_points = landmarks[upper_lip]
                lower_points = landmarks[lower_lip]
                
                # 입 중심점
                mouth_center = np.mean(np.vstack([upper_points, lower_points]), axis=0).astype(int)
                
                # 상하 입술을 반대 방향으로 이동
                scaled_upper = []
                scaled_lower = []
                
                for point in upper_points:
                    vector = point - mouth_center
                    # 상 입술은 위로
                    scaled_vector = vector * [1.0, 1.0 - mouth_openness * 0.3]
                    scaled_upper.append(mouth_center + scaled_vector.astype(int))
                
                for point in lower_points:
                    vector = point - mouth_center
                    # 하 입술은 아래로
                    scaled_vector = vector * [1.0, 1.0 + mouth_openness * 0.3]
                    scaled_lower.append(mouth_center + scaled_vector.astype(int))
                
                # 입술 영역 그리기
                all_points = np.array(scaled_upper + scaled_lower)
                
                # 더 자연스러운 입술 색상과 블렌딩
                mask = np.zeros(animated_image.shape[:2], dtype=np.uint8)
                cv2.fillPoly(mask, [all_points], 255)
                
                # 원본 입술 색상 추출
                original_lip_color = np.mean(animated_image[mask > 0], axis=0)
                
                # 입 열림에 따른 어두운 효과 (입 안쪽)
                if mouth_openness > 0.3:
                    inner_color = original_lip_color * 0.3  # 어두운 입 안쪽
                    animated_image[mask > 0] = inner_color
                
                # 부드러운 블렌딩
                blurred_mask = cv2.GaussianBlur(mask.astype(np.float32), (3, 3), 0)
                blurred_mask = np.stack([blurred_mask] * 3, axis=-1) / 255.0
                
                animated_image = animated_image.astype(np.float32)
                animated_image = animated_image * (1 - blurred_mask * 0.3) + \
                               (animated_image * blurred_mask * 0.7)
                animated_image = np.clip(animated_image, 0, 255).astype(np.uint8)
            
            return animated_image
            
        except Exception as e:
            self.logger.error(f"입 애니메이션 실패: {e}")
            # 실패 시 밝기 변화라도 적용
            brightness = 1.0 + (mouth_openness * 0.1)
            return cv2.convertScaleAbs(image, alpha=brightness, beta=0)
    
    def create_lipsync_video(self, face_image_path: str, audio_path: str, 
                           output_path: str, fps: int = 30) -> bool:
        """얼굴 이미지와 오디오로 립싱크 비디오를 생성합니다 (자막 없음)"""
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
            
            # 오디오 클립 길이를 비디오와 맞춤
            if audio_clip.duration > video_clip.duration:
                audio_clip = audio_clip.subclip(0, video_clip.duration)
            elif audio_clip.duration < video_clip.duration:
                video_clip = video_clip.subclip(0, audio_clip.duration)
            
            final_clip = video_clip.set_audio(audio_clip)
            
            # 더 호환성 높은 설정으로 저장
            final_clip.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False, 
                logger=None
            )
            
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