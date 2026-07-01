import math
from gameconfig import ELBOW_T


def elbow_angle(a, b, c) -> float:
    ba = [a.x - b.x, a.y - b.y]
    bc = [c.x - b.x, c.y - b.y]
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    mag_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    mag_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)
    cos_v = dot / (mag_ba * mag_bc + 1e-6)
    cos_v = max(-1.0, min(1.0, cos_v))
    return math.degrees(math.acos(cos_v))


def hand_angle(shoulder, wrist) -> float:
    dx = wrist.x - shoulder.x
    dy = shoulder.y - wrist.y
    return math.degrees(math.atan2(dy, dx))


def distance(p1, p2) -> float:
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def detect_pose(lm) -> str:
    """Return LEFT, RIGHT, UP, DOWN, RELEASE, or NONE from MediaPipe landmarks."""
    ls, rs = lm[11], lm[12]
    le, re = lm[13], lm[14]
    lw, rw = lm[15], lm[16]
    lear, rear = lm[7], lm[8]

    e_l = elbow_angle(ls, le, lw)
    e_r = elbow_angle(rs, re, rw)
    arms_straight = e_l > ELBOW_T and e_r > ELBOW_T

    a_l = hand_angle(ls, lw)
    a_r = hand_angle(rs, rw)
    angle = (a_l + a_r) / 2

    shoulder_y = (ls.y + rs.y) / 2
    hands_up = lw.y < shoulder_y and rw.y < shoulder_y
    shoulder_width = distance(ls, rs)
    elbow_span = distance(le, re)
    wrist_dist = distance(lw, rw)
    shoulder_center_x = (ls.x + rs.x) / 2
    wrist_center_x = (lw.x + rw.x) / 2
    ear_center_x = (lear.x + rear.x) / 2

    wrists_near_shoulder_height = abs(lw.y - shoulder_y) < 0.12 and abs(rw.y - shoulder_y) < 0.12
    elbows_near_shoulder_height = abs(le.y - shoulder_y) < 0.12 and abs(re.y - shoulder_y) < 0.12
    left_arm_forward = lw.z < ls.z - 0.12 and le.z < ls.z - 0.06
    right_arm_forward = rw.z < rs.z - 0.12 and re.z < rs.z - 0.06
    wrists_level = abs(lw.y - rw.y) < 0.12

    # Forward arm pose = answer C.
    if wrists_near_shoulder_height and elbows_near_shoulder_height and left_arm_forward and right_arm_forward and wrists_level:
        return "UP"

    # Back elbow pose = answer D.
    elbows_open_wide = elbow_span > shoulder_width * 1.08
    elbows_bent = e_l < 100 and e_r < 100
    elbows_near_head = distance(le, lear) < 0.28 and distance(re, rear) < 0.28
    head_centered = abs(ear_center_x - shoulder_center_x) < 0.10
    not_side_bending = 75 <= angle <= 105
    if elbows_open_wide and elbows_bent and elbows_near_head and head_centered and not_side_bending:
        return "DOWN"

    # Arm rise is used as RELEASE. Tilted arm rise is used for LEFT/RIGHT.
    if hands_up and arms_straight:
        wrists_close = wrist_dist < shoulder_width * 1
        elbows_not_too_wide = elbow_span < shoulder_width * 1.2
        elbows_up = le.y < ls.y + 0.08 and re.y < rs.y + 0.08
        if wrists_close and elbows_not_too_wide and elbows_up and 85 <= angle <= 95:
            return "RELEASE"
        if wrists_close and elbows_not_too_wide and elbows_up and angle > 115 and wrist_center_x < shoulder_center_x - 0.02:
            return "LEFT"
        if wrists_close and elbows_not_too_wide and elbows_up and angle < 65 and wrist_center_x > shoulder_center_x + 0.02:
            return "RIGHT"

    return "NONE"
