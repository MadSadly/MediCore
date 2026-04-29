package com.example.backend_main.auth;

import com.example.backend_main.auth.dto.AuthResponse;
import com.example.backend_main.auth.dto.LoginRequest;
import com.example.backend_main.auth.dto.RegisterRequest;
import com.example.backend_main.hospital.HospitalStaff;
import com.example.backend_main.hospital.HospitalStaffRepository;
import com.example.backend_main.user.User;
import com.example.backend_main.user.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final HospitalStaffRepository hospitalStaffRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtUtil jwtUtil;

    public void register(RegisterRequest req) {
        // 1. 병원 직원 테이블에서 병원코드 + 사원번호로 조회
        HospitalStaff staff = hospitalStaffRepository
            .findByHospitalCodeAndEmployeeNumber(req.getHospitalCode(), req.getEmployeeNumber())
            .orElseThrow(() -> new ResponseStatusException(
                HttpStatus.UNAUTHORIZED,
                "병원 직원 정보를 찾을 수 없습니다. 병원코드 또는 사원번호를 확인하세요."));

        // 2. 주민등록번호 또는 의사면허번호 일치 확인
        boolean ssnMatch     = passwordEncoder.matches(req.getSsnOrLicense(), staff.getSsnHash());
        boolean licenseMatch = staff.getLicenseNumberHash() != null
            && passwordEncoder.matches(req.getSsnOrLicense(), staff.getLicenseNumberHash());

        if (!ssnMatch && !licenseMatch) {
            throw new ResponseStatusException(
                HttpStatus.UNAUTHORIZED,
                "주민등록번호 또는 의사면허번호가 일치하지 않습니다.");
        }

        // 3. 이메일 중복 확인
        if (userRepository.existsByEmail(req.getEmail())) {
            throw new ResponseStatusException(HttpStatus.CONFLICT, "이미 사용 중인 이메일입니다.");
        }

        // 4. 계정 생성 (이름은 병원 직원 테이블 기준, 병원 소속 정보 함께 저장)
        User user = User.builder()
            .name(staff.getName())
            .email(req.getEmail())
            .password(passwordEncoder.encode(req.getPassword()))
            .hospitalCode(req.getHospitalCode())
            .employeeNumber(req.getEmployeeNumber())
            .build();
        userRepository.save(user);
    }

    public AuthResponse login(LoginRequest req) {
        User user = userRepository.findByEmail(req.getEmail())
            .orElseThrow(() -> new ResponseStatusException(
                HttpStatus.UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다."));
        if (!passwordEncoder.matches(req.getPassword(), user.getPassword())) {
            throw new ResponseStatusException(
                HttpStatus.UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다.");
        }
        String token = jwtUtil.generate(user.getEmail());
        return new AuthResponse(token, user.getName(), user.getEmail());
    }
}