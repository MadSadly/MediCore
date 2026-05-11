package com.example.backend_main.GW;

import com.example.backend_main.GW.ColonResult;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface ColonResultRepository extends JpaRepository<ColonResult, Long> {
    List<ColonResult> findByPatientUidOrderByCreatedAtDesc(String patientUid);
}