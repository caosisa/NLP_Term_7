#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import requests
from datetime import datetime, date
import calendar
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import torch.nn as nn
from tqdm import tqdm
import time
import os

# 환경변수로 설정
os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # GPU 1번만 사용

class CompleteCampusKnowledgeBase:
    """완전한 캠퍼스 지식 베이스 (정적 + 실시간)"""

    def __init__(self):
        self.setup_static_knowledge()
        self.cache = {}
        self.cache_timeout = 1800  # 30분 캐시

    def setup_static_knowledge(self):
        """정적 지식 (항상 정확한 기본 정보)"""
        self.static_knowledge = {
            "graduation": {
                "overview": {
                    "university": "충남대학교",
                    "legal_basis": "충남대학교 학칙 제53조",
                    "standard_credits": 130,
                    "note": "학문의 특성상 필요한 경우 학과별로 따로 정할 수 있음",
                    "contact": "학사지원과 042-821-5025",
                    "website": "충남대 홈페이지 > 학사정보 > 교육과정"
                },

                "basic_structure": {
                    "course_categories": {
                        "교양과목": {
                            "description": "대학 졸업자가 갖추어야 할 지도적 인격을 도야함에 필요한 과목",
                            "minimum_credits": 36,
                            "types": ["공통기초교양", "핵심교양", "일반교양", "전문기초교양", "특별교양"]
                        },
                        "전공과목": {
                            "description": "전문학술연구에 직접 필요로 하는 과목",
                            "types": ["전공기초", "전공핵심", "전공심화"],
                            "note": "전공핵심과 전공심화는 상호 인정 가능"
                        },
                        "일반선택과목": {
                            "description": "군사학관련, 봉사관련, 평생교육사관련 교과목 등"
                        }
                    },

                    "credit_distribution_by_type": {
                        "단수전공자": {
                            "total_credits": 130,
                            "교양": 36,
                            "전공": "54-90 (학과별 상이)",
                            "일반선택": "4-40 (학과별 상이)"
                        },
                        "복수전공자": {
                            "total_credits": 130,
                            "교양": 36,
                            "주전공": "45-55 (학과별 상이)",
                            "복수전공": "36학점 이상",
                            "일반선택": "나머지 학점"
                        },
                        "부전공자": {
                            "total_credits": 130,
                            "교양": 36,
                            "전공": 54,
                            "부전공": "21학점 이상",
                            "일반선택": 40
                        }
                    }
                },

                "liberal_arts_detailed": {
                    "total_credits": 36,
                    "completion_period": "1~2학년 중심",
                    "maximum_recognition": "42학점까지만 인정 (초과 시 졸업학점 불인정)",

                    "mandatory_courses": {
                        "공통기초교양": {
                            "credits": 8,
                            "courses": {
                                "기초글쓰기": "2학점 (필수)",
                                "대학영어1": "2학점",
                                "대학영어2": "2학점",
                                "대학생활과진로설계": "1학점 (필수)",
                                "취업과창업": "1학점 (필수)"
                            }
                        },

                        "핵심교양": {
                            "credits": 9,
                            "requirement": "6개 역량 중 최소 3개 역량에서 각 1과목씩",
                            "competencies": {
                                "창의융합": ["공학입문", "지식사회와정보활용", "빅데이터의이해와활용"],
                                "글로벌": ["공학도를위한세계문화", "현대인의생활문화", "서양의역사와문화"],
                                "의사소통": ["공학논문작성과발표", "경제의이해", "논리와비판적사고"],
                                "자기관리": ["공학윤리", "컴퓨터이해와활용", "심리학개론"],
                                "인성": ["정신건강", "한문고전과삶의지혜", "현대인의경제활동과법률"],
                                "대인관계": ["사이버공간과윤리", "역사와리더십", "인간관계론"]
                            }
                        },

                        "전문기초교양": {
                            "credits": "학과별 지정",
                            "common_courses": ["미적분학1", "물리학개론", "생물학", "컴퓨터과학적사고"]
                        },

                        "일반교양": {
                            "credits": "나머지 학점",
                            "areas": ["언어·문학", "역사·철학", "사회과학", "자연과학", "예술·체육", "융복합"]
                        }
                    },

                    "special_requirements": {
                        "인문학관련": {
                            "requirement": "8학점 이상 이수",
                            "note": "기초글쓰기 2학점 포함"
                        },
                        "소프트웨어관련": {
                            "applicable_from": "2022학년도 이후 입학자",
                            "requirement": "1과목 필수 이수",
                            "courses": [
                                "컴퓨터과학적사고", "컴퓨터이해와활용", "정보보호입문과활용",
                                "파이썬프로그래밍", "데이터분석입문과활용", "프로그래밍언어",
                                "인공지능개론", "인공지능과미래사회", "인공지능융합기초",
                                "웹프로그래밍기초", "C프로그래밍기초", "가상현실이해와활용"
                            ]
                        }
                    }
                },

                "english_requirements": {
                    "수능등급별_이수": {
                        "1등급": {
                            "수강과목": "대학영어2만",
                            "추가이수": "핵심교양 또는 일반교양 중 2학점"
                        },
                        "2~9등급": {
                            "수강과목": "대학영어1, 2 순차 이수"
                        }
                    },
                    "공인영어시험_면제기준": {
                        "TOEIC": "800점 이상",
                        "TOEFL_IBT": "91점 이상",
                        "NEW_TEPS": "309점 이상",
                        "TOEIC_Speaking": "130점 이상",
                        "OPIc": "IM3 이상",
                        "IELTS": "7점 이상"
                    },
                    "특별조치": {
                        "외국인전형입학생": "대학영어 수강 불가, 한국어1,2 필수",
                        "청각장애학생": "대학영어1,2 이수 면제"
                    }
                },

                "major_requirements_by_department": {
                    "컴퓨터융합학부": {
                        "total_credits": 130,
                        "단수전공": {
                            "교양": 36,
                            "전공기초": 18,
                            "전공핵심": 26,
                            "전공심화": 46,
                            "일반선택": 4
                        },
                        "복수전공": {
                            "교양": 36,
                            "전공": 54,
                            "일반선택": 40
                        },
                        "required_courses": {
                            "전공기초": [
                                "컴퓨터프로그래밍1", "컴퓨터프로그래밍2", "확률및통계",
                                "자료구조", "컴퓨터구조", "알고리즘"
                            ]
                        },
                        "special_requirements": {
                            "track_completion": "9개 트랙 중 1개 이상",
                            "project_courses": "3개 교과목 이상 이수",
                            "portfolio": "필수",
                            "graduation_thesis": "필수"
                        },
                        "tracks": [
                            "인공지능", "빅데이터", "웹/모바일개발자", "컴퓨터시스템",
                            "사이버보안", "데이터아키텍트", "컴퓨터하드웨어", "클라우드/인프라", "자기설계"
                        ]
                    },

                    "인공지능학과": {
                        "total_credits": 130,
                        "단수전공": {
                            "교양": 36,
                            "전공기초": 15,
                            "전공핵심": 24,
                            "전공심화": 39,
                            "일반선택": 16
                        },
                        "required_courses": {
                            "전공기초": [
                                "이산수학", "자료구조", "AI활용표현과문제해결",
                                "기계학습", "컴퓨터프로그래밍1", "알고리즘"
                            ]
                        }
                    },

                    "일반_학과": {
                        "인문대학": {
                            "total_credits": 130,
                            "교양": 36,
                            "전공": 78,
                            "일반선택": 16
                        },
                        "자연과학대학": {
                            "total_credits": 130,
                            "교양": 36,
                            "전공": 81,
                            "일반선택": 13
                        },
                        "공과대학": {
                            "total_credits": 130,
                            "교양": 36,
                            "전공": 90,
                            "일반선택": 4
                        }
                    }
                },

                "grade_requirements": {
                    "일반학생": "전체 교과목 성적의 평점평균 1.75 이상",
                    "대학원연계과정": "전체 교과목 성적의 평점평균 3.75 이상",
                    "조기졸업": "전체 교과목 성적의 평점평균 4.0 이상"
                },

                "additional_requirements": {
                    "future_design_counseling": {
                        "일반학생": "5회 이상 필수",
                        "편입생": "2회 이상",
                        "의예과_수의예과": "2회 이상",
                        "재입학생": {
                            "1학년": "5회 이상",
                            "2학년": "4회 이상",
                            "3학년": "3회 이상",
                            "4학년_이상": "1회 이상"
                        }
                    },

                    "special_programs": {
                        "교직과정": {
                            "단수전공": "140학점",
                            "복수전공": "150학점",
                            "note": "교직과목 별도 이수"
                        },
                        "평생교육사과정": "관련 과목 추가 이수",
                        "마이크로디그리과정": "특정 분야 집중 이수"
                    }
                },

                "special_cases": {
                    "의과대학": {
                        "의예과": "72학점 (수료학점)",
                        "의학과": "164학점",
                        "note": "복수전공 제한"
                    },
                    "수의과대학": {
                        "수의예과": "72학점 (수료학점)",
                        "수의학과": "160학점",
                        "note": "복수전공 제한"
                    },
                    "약학대학": {
                        "약학과": "232학점",
                        "note": "복수전공 제한"
                    },
                    "건축학과": {
                        "total_credits": 166,
                        "note": "건축학교육프로그램인증 기준"
                    }
                },

                "important_notes": [
                    "교양과목은 42학점까지만 인정하며 초과 시 졸업학점으로 인정하지 않음",
                    "전공핵심과 전공심화는 상호 인정되어 구분없이 이수 가능",
                    "전공기초는 상호 인정되지 않아 필히 최소학점 이상 이수",
                    "이수면제로 부족한 학점은 일반, 핵심교양에서 추가 이수",
                    "복수전공자는 복수전공 학과의 전공과목을 추가로 이수",
                    "부전공자는 부전공 학과의 전공과목 21학점 이상 이수",
                    "학과별 세부 요건은 소속 학과에서 별도 확인 필요"
                ],

                "contact_information": {
                    "학사지원과": {
                        "phone": "042-821-5025",
                        "services": ["졸업요건 상담", "학적 관리", "성적 관리"]
                    },
                    "각_학과_사무실": {
                        "services": ["학과별 세부 요건", "전공 관련 상담", "트랙 이수 상담"]
                    },
                    "학생지원과": {
                        "phone": "042-821-5015",
                        "services": ["장학금", "등록금", "복수전공 신청"]
                    }
                },

                "useful_tips": [
                    "졸업요건은 입학년도 기준으로 적용됩니다",
                    "전공 변경 시 변경된 학과 기준으로 적용됩니다",
                    "미리 학점 계획을 세워 부족한 영역을 파악하세요",
                    "교양과목 42학점 제한에 주의하세요",
                    "트랙 이수나 복수전공 계획이 있다면 미리 상담받으세요",
                    "졸업논문이나 포트폴리오 요구사항을 미리 확인하세요"
                ]
            },

            "academic_schedule": {
                "overview": {
                    "academic_year": "2025학년도",
                    "semester_system": "2학기제 (1학기: 3월~6월, 2학기: 9월~12월)",
                    "total_weeks": "각 학기 15주 수업 + 시험기간",
                    "contact": "학사지원과 042-821-5025",
                    "website": "충남대 홈페이지(www.cnu.ac.kr) > 학사정보",
                    "portal": "CNU 포털시스템(portal.cnu.ac.kr)"
                },

                "first_semester": {
                    "name": "2025학년도 제1학기",
                    "period": "2025년 3월 4일(화) ~ 2025년 6월 23일(월)",

                    "registration": {
                        "pre_registration": {
                            "period": "2025년 1월 31일(금) ~ 2월 3일(월)",
                            "target": "재학생 대상 예비수강신청",
                            "system": "CNU 포털시스템",
                            "notes": "실제 수강신청 전 미리 신청해보는 기간"
                        },
                        "main_registration": {
                            "period": "2025년 2월 5일(수) ~ 2월 11일(화)",
                            "time": "학년별 지정 시간대",
                            "system": "CNU 포털시스템(portal.cnu.ac.kr)",
                            "priority": "졸업예정자 > 고학년 > 저학년 순",
                            "notes": "시간표 충돌 및 수강인원 제한 확인 필요"
                        },
                        "confirmation_change": {
                            "period": "2025년 3월 4일(화) ~ 3월 10일(월)",
                            "description": "개강 후 수강신청 확인 및 변경 기간",
                            "notes": "실제 수업 참여 후 변경 가능"
                        },
                        "cancellation": {
                            "period": "2025년 3월 24일(월) ~ 3월 27일(목)",
                            "description": "수강신청 취소 기간",
                            "effect": "성적표에 기록되지 않음",
                            "deadline": "3월 27일 18:00까지"
                        }
                    },

                    "tuition": {
                        "payment_period": "2025년 2월 25일(화) ~ 2월 28일(금)",
                        "target": "재학생 등록금 납부",
                        "method": "은행 방문, 인터넷뱅킹, 가상계좌",
                        "late_fee": "납부 지연 시 연체료 부과",
                        "contact": "학생지원과 042-821-5015"
                    },

                    "semester_dates": {
                        "start_date": "2025년 3월 4일(화)",
                        "classes_start": "3월 4일부터 정규 수업 시작",
                        "quarter_point": "3월 28일 (수업일수 1/4선)",
                        "third_point": "4월 7일 (수업일수 1/3선)",
                        "half_point": "4월 24일 (수업일수 1/2선)",
                        "two_thirds_point": "5월 15일 (수업일수 2/3선)",
                        "three_quarters_point": "5월 26일 (수업일수 3/4선)",
                        "last_class": "6월 23일 정규수업 종료"
                    },

                    "exam_periods": {
                        "midterm": {
                            "period": "2025년 4월 중순 (정확한 날짜는 학과별 공지)",
                            "duration": "보통 1주일",
                            "notes": "중간고사 기간 중 정규수업 없음"
                        },
                        "final": {
                            "period": "2025년 6월 중순 (정확한 날짜는 학과별 공지)",
                            "duration": "보통 1주일",
                            "notes": "기말고사 후 학기 종료"
                        }
                    },

                    "grade_announcement": {
                        "date": "2025년 7월 11일(금)",
                        "method": "CNU 포털시스템에서 확인",
                        "objection_period": "성적 이의신청 기간 별도 공지",
                        "contact": "학사지원과 042-821-5025"
                    },

                    "vacation": {
                        "start_date": "2025년 6월 24일(화)",
                        "name": "하기방학 (여름방학)",
                        "duration": "약 2개월",
                        "summer_session": {
                            "period": "6월 24일 ~ 7월 14일",
                            "registration": "5월 8일 ~ 5월 12일",
                            "description": "하기 계절학기 운영"
                        }
                    }
                },

                "second_semester": {
                    "name": "2025학년도 제2학기",
                    "period": "2025년 9월 1일(월) ~ 2025년 12월 21일(일)",

                    "registration": {
                        "pre_registration": {
                            "period": "2025년 7월 28일(월) ~ 7월 30일(수)",
                            "target": "재학생 대상 예비수강신청",
                            "system": "CNU 포털시스템"
                        },
                        "main_registration": {
                            "period": "2025년 8월 4일(월) ~ 8월 8일(금)",
                            "time": "학년별 지정 시간대",
                            "system": "CNU 포털시스템(portal.cnu.ac.kr)"
                        },
                        "confirmation_change": {
                            "period": "2025년 9월 1일(월) ~ 9월 5일(금)",
                            "description": "개강 후 수강신청 확인 및 변경 기간"
                        },
                        "cancellation": {
                            "period": "2025년 9월 22일(월) ~ 9월 25일(목)",
                            "description": "수강신청 취소 기간",
                            "deadline": "9월 25일 18:00까지"
                        }
                    },

                    "tuition": {
                        "payment_period": "2025년 8월 26일(화) ~ 8월 29일(금)",
                        "target": "재학생 등록금 납부"
                    },

                    "semester_dates": {
                        "start_date": "2025년 9월 1일(월)",
                        "quarter_point": "9월 25일 (수업일수 1/4선)",
                        "third_point": "10월 10일 (수업일수 1/3선)",
                        "half_point": "10월 29일 (수업일수 1/2선)",
                        "two_thirds_point": "11월 14일 (수업일수 2/3선)",
                        "three_quarters_point": "11월 25일 (수업일수 3/4선)",
                        "last_class": "12월 21일 정규수업 종료"
                    },

                    "exam_periods": {
                        "midterm": {
                            "period": "2025년 10월 중순",
                            "duration": "보통 1주일"
                        },
                        "final": {
                            "period": "2025년 12월 중순",
                            "duration": "보통 1주일"
                        }
                    },

                    "vacation": {
                        "start_date": "2025년 12월 22일(일)",
                        "name": "동기방학 (겨울방학)",
                        "duration": "약 2개월",
                        "winter_session": {
                            "period": "12월 22일 ~ 2026년 1월 13일",
                            "registration": "11월 7일 ~ 11월 11일",
                            "description": "동기 계절학기 운영"
                        }
                    }
                },

                "special_applications": {
                    "leave_return": {
                        "first_semester": "2025년 2월 3일 ~ 2월 28일",
                        "second_semester": "2025년 8월 1일 ~ 8월 29일",
                        "description": "휴학 및 복학 신청",
                        "contact": "학사지원과 042-821-5025"
                    },

                    "early_graduation": {
                        "first_semester": "2025년 3월 31일 ~ 4월 4일",
                        "second_semester": "2025년 9월 25일 ~ 10월 2일",
                        "description": "조기졸업 신청",
                        "requirements": "평점평균 3.75 이상, 소정 학점 이수"
                    },

                    "thesis_deferral": {
                        "periods": [
                            "2025년 1월 20일 ~ 1월 24일",
                            "2025년 3월 4일 ~ 3월 11일 (취소)",
                            "2025년 7월 21일 ~ 7월 25일",
                            "2025년 9월 1일 ~ 9월 8일 (취소)"
                        ],
                        "description": "학사학위취득 유예 신청 및 취소"
                    },

                    "convergence_major": {
                        "first_semester": "2025년 4월 7일 ~ 4월 11일",
                        "second_semester": "2025년 10월 13일 ~ 10월 17일",
                        "description": "융복합창의전공 신청 및 취소"
                    },

                    "curriculum_change": {
                        "first_semester": "2025년 3월 4일 ~ 3월 31일",
                        "second_semester": "2025년 9월 1일 ~ 9월 30일",
                        "description": "교육과정 적용연도 및 소속 변경"
                    }
                },

                "ceremonies_events": {
                    "entrance_ceremony": {
                        "date": "2025년 2월 28일(금)",
                        "description": "2025학년도 입학식",
                        "location": "충남대학교 대강당 (예정)"
                    },

                    "graduation_ceremonies": {
                        "february": {
                            "date": "2025년 2월 25일(화)",
                            "description": "2024년도 전기 학위수여식"
                        },
                        "august": {
                            "date": "2025년 8월 25일(월)",
                            "description": "2024년도 후기 학위수여식"
                        }
                    },

                    "founding_day": {
                        "date": "2025년 5월 25일(일)",
                        "description": "충남대학교 개교기념일",
                        "note": "수업 및 셔틀버스 운행 없음"
                    }
                },

                "important_notes": [
                    "모든 일정은 학교 사정에 따라 변경될 수 있습니다",
                    "정확한 시험 일정은 각 학과 및 담당 교수님께 확인하세요",
                    "수강신청은 지정된 시간에만 가능하며, 서버 과부하에 주의하세요",
                    "등록금 납부 기한을 넘기면 자동 제적될 수 있습니다",
                    "공휴일이 겹치는 경우 일정이 조정될 수 있습니다",
                    "계절학기는 별도 수강료가 부과됩니다"
                ],

                "helpful_tips": [
                    "수강신청 전 미리 시간표를 계획해보세요",
                    "인기 과목은 수강신청 시작과 동시에 마감될 수 있습니다",
                    "졸업요건을 미리 확인하여 필요한 과목을 파악하세요",
                    "성적 이의신청은 정해진 기간 내에만 가능합니다",
                    "휴학 시 복학 시기를 미리 계획하세요"
                ],

                "contact_info": {
                    "학사지원과": {
                        "phone": "042-821-5025",
                        "services": ["졸업요건", "학사일정", "수강신청", "성적관리"]
                    },
                    "학생지원과": {
                        "phone": "042-821-5015",
                        "services": ["등록금", "장학금", "학적관리"]
                    },
                    "각_학과_사무실": {
                        "services": ["전공 관련 상담", "시험 일정", "졸업논문"]
                    }
                },

                "online_systems": {
                    "cnu_portal": {
                        "url": "portal.cnu.ac.kr",
                        "services": ["수강신청", "성적조회", "학적조회", "증명서 발급"]
                    },
                    "main_website": {
                        "url": "www.cnu.ac.kr",
                        "services": ["공지사항", "학사일정", "학교소식"]
                    }
                }
            },

            "dining": {
                "student_restaurant": {
                    "location": "제 1학생회관",
                    "korean": "한식 평균 4,000원",
                    "western": "양식 평균 5,000원",
                    "chinese": "중식 평균 5,500원",
                    "special": "특식 평균 6,000원"
                },
                "faculty_restaurant": {
                    "location": "제 2학생회관",
                    "price": "4,500원"
                },
                "cafeteria": {
                    "location": "정심화국제문화회관 1층",
                    "menu": "커피, 간식, 샐러드"
                },
                "hours": {
                    "breakfast": "08:00-09:30 (평일, 일부 식당)",
                    "lunch": "11:30-14:00",
                    "dinner": "17:30-19:00"
                },
                "more_info":"식단표 확인은 2일뒤까지만 공개됩니다.",
                "weekend": "주말에는 식당이 운영하지 않습니다.",
                "info_source": "생협 홈페이지(coop.cnu.ac.kr)에서 식단을 확인하세요.",
                "contact": "생활협동조합(042-821-5890)으로 문의하세요."
            },

            "shuttle": {
                "operation_overview": {
                    "period": "2025. 3. 4.(화) ~ 2025. 12. 19.(금), 총 150일",
                    "location": "교내(대덕캠퍼스) 및 캠퍼스 순환(대덕↔보운)",
                    "buses": "학교버스 총 2대, 41인승",
                    "operation_days": "학기 중 주간 운영(월~금)",
                    "non_operation": "공휴일·대체공휴일·개교기념일·방학·수학능력시험일(10시 이전까지) 등 미운영"
                },

                "campus_internal": {
                    "name": "교내 순환 (대덕캠퍼스 내)",
                    "operation_period": "학기 중 3.4.～12.19. 총 150일 (월～금)",
                    "buses": "1대",
                    "frequency": "1일 총 10회 운영",
                    "first_bus": "08:30",
                    "last_bus": "17:30",
                    "morning_special": "등교 1회차: 월평역 출발 08:20 → 정심화 국제문화회관 도착",
                    "schedule": [
                        "08:30", "09:30", "09:40", "10:30", "11:30",
                        "13:30", "14:30", "15:30", "16:30", "17:30"
                    ],

                    "route_stops": [
                        "정심화 국제문화회관", "사회과학대학 입구(한누리회관 뒤)",
                        "서문(공동실험실습관 앞)", "음악 2호관 앞", "공동동물실험센터(회차)",
                        "체육관 입구", "예술대학 앞", "도서관 앞(대학본부 옆)", "학생생활관 3거리",
                        "농업생명과학대학 앞", "동문주차장"
                    ]
                },

                "campus_circulation": {
                    "name": "캠퍼스 순환 (대덕↔보운)",
                    "operation_period": "학기 중 (월～금)",
                    "buses": "1대",
                    "frequency": "1일 총 1회 운영 (회차)",
                    "departure": "08:10 (대덕 골프연습장)",
                    "arrival": "08:50 (보운캠퍼스)",
                    "route": "골프연습장(08:10) → 중앙도서관(08:11) → 산학연교육연구관(08:12) → 충남대입구 버스정류장(08:13) → 월평역(08:15) → 보운캠퍼스(08:50)",
                    "return_route": "보운캠퍼스 → 다솔아파트 건너편 → 제2학생회관 → 중앙도서관 → 골프연습장"
                },

                "external_stops": {
                    "월평역": "3번 출구 건너편(테니스장 앞 버스정류장 부근)",
                    "충남대입구": "버스정류장(홈플러스유성점방면)",
                    "보운캠퍼스": "회차지점",
                    "다솔아파트": "건너편"
                },

                "important_notes": [
                    "교통상황 등으로 인해 전 구간에서 5분 내외 오차 발생 가능",
                    "탑승자는 사전 대기 필요",
                    "학교 버스가 보이면 탑승 의사를 알려주세요",
                    "운행시간은 천재지변, 학교행사, 교통상황, 탑승 인원 등에 따라 변경 가능",
                    "세부 운행시간은 이용자 및 운행 추이에 따라 논의를 거쳐 변동 가능"
                ],

                "contact": "총무과(042-821-5114) 또는 학생처 학생과",
                "last_updated": "2025. 2. 18.(화), 학생처 학생과"
            },

            "notice": {
                "main_website": "충남대 홈페이지(www.cnu.ac.kr)에서 확인하세요.",
                "portal": "CNU 포털시스템에서도 중요 공지를 받을 수 있습니다.",
                "department": "각 학과 홈페이지에서 학과별 공지를 확인하세요.",
                "scholarship": "장학금 공지는 학생지원과에서 담당합니다.",
                "student_council": "총학생회 공지는 총학생회 홈페이지에서 확인하세요.",
                "contacts": {
                    "학사지원과": "042-821-5025",
                    "학생지원과": "042-821-5015"
                }
            },

            "contacts": {
                "학사지원과": "042-821-5025 (졸업요건, 학사일정)",
                "학생지원과": "042-821-5015 (장학금, 학생활동)",
                "총무과": "042-821-5114 (셔틀버스, 시설)",
                "생활협동조합": "042-821-5890 (식당, 매점)",
                "도서관": "042-821-5092",
                "정보통신원": "042-821-6851"
            }
        }

    def extract_date_from_question(self, question):
        """질문에서 날짜 추출"""
        import re
        from datetime import timedelta

        # 어제
        if any(word in question.lower() for word in ['어제', 'yesterday']):
            yesterday = date.today() - timedelta(days=1)
            return yesterday.strftime("%Y.%m.%d")

        # 오늘, 지금
        if any(word in question.lower() for word in ['오늘', 'today', '지금']):
            return None  # None이면 오늘 날짜 사용

        # 내일
        if any(word in question.lower() for word in ['내일', 'tomorrow']):
            tomorrow = date.today() + timedelta(days=1)
            return tomorrow.strftime("%Y.%m.%d")

        # 모레
        if any(word in question.lower() for word in ['모레']):
            day_after_tomorrow = date.today() + timedelta(days=2)
            return day_after_tomorrow.strftime("%Y.%m.%d")

        # 이번 주 요일들
        weekday_patterns = {
            '월요일': 0, '화요일': 1, '수요일': 2, '목요일': 3,
            '금요일': 4, '토요일': 5, '일요일': 6
        }

        for weekday_name, weekday_num in weekday_patterns.items():
            if weekday_name in question:
                today = date.today()
                days_ahead = weekday_num - today.weekday()

                # 이번 주 해당 요일이 지났으면 다음 주
                if days_ahead <= 0:
                    days_ahead += 7

                target_date = today + timedelta(days=days_ahead)
                return target_date.strftime("%Y.%m.%d")

        # 숫자 날짜 패턴 (2024.12.25, 2024-12-25, 12/25 등)
        date_patterns = [
            r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})',  # YYYY.MM.DD
            r'(\d{1,2})[.\-/](\d{1,2})',  # MM.DD (올해)
        ]

        for pattern in date_patterns:
            match = re.search(pattern, question)
            if match:
                groups = match.groups()
                if len(groups) == 3:
                    year, month, day = groups
                    return f"{year}.{month.zfill(2)}.{day.zfill(2)}"
                elif len(groups) == 2:
                    month, day = groups
                    current_year = date.today().year
                    return f"{current_year}.{month.zfill(2)}.{day.zfill(2)}"

        # 날짜를 찾지 못하면 None (오늘 날짜 사용)
        return None

    def fetch_today_menu(self, date_str=None):
        """식단 크롤링 - 날짜 자동 처리"""

        # 1. 날짜 처리 개선
        if date_str is None:
            # 날짜가 없으면 오늘 날짜 사용
            print("date_str정보없음")
            today = date.today()
            date_str = today.strftime("%Y.%m.%d")
        else:
            # 다양한 날짜 형식 처리
            date_str = self.normalize_date_format(date_str)

        print(f"🍽️ {date_str} 식단 크롤링 중...")

        try:
            url = f"https://mobileadmin.cnu.ac.kr/food/index.jsp?searchYmd={date_str}&searchLang=OCL04.10&searchView=cafeteria&searchCafeteria=OCL03.02&Language_gb=OCL04.10"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            response.encoding = "utf-8"

            soup = BeautifulSoup(response.text, "html.parser")
            table = soup.find("table", class_="menu-tbl type-cap")

            if not table:
                print("⚠️ 식단표를 찾을 수 없습니다.")

            meals = []
            current_meal_type = None

            # 식당명 추출 (제2학생회관부터)
            headers = table.find("thead")
            if not headers:
                print("2학 x")

            header_cells = headers.find_all("th")[2:]  # 구분, 제1학생회관 제외
            cafeteria_names = [th.get_text(strip=True) for th in header_cells]

            # 메뉴 데이터 추출
            tbody = table.find("tbody")
            if not tbody:
                print("메뉴x")

            rows = tbody.find_all("tr")

            for row in rows:
                cols = row.find_all("td")
                if not cols:
                    continue

                # rowspan이 있는 경우 (새로운 식사 타입)
                if len(cols) > 0 and 'rowspan' in cols[0].attrs:
                    current_meal_type = cols[0].get_text(strip=True)
                    if len(cols) > 1:
                        current_target = cols[1].get_text(strip=True)
                        menu_cols = cols[2:] if len(cols) > 2 else []
                    else:
                        current_target = "전체"
                        menu_cols = []
                else:
                    # rowspan이 없는 경우
                    if len(cols) > 0:
                        current_target = cols[0].get_text(strip=True)
                        menu_cols = cols[1:] if len(cols) > 1 else []
                    else:
                        continue

                # 각 식당별 메뉴 처리
                for idx, col in enumerate(menu_cols):
                    if idx >= len(cafeteria_names):
                        continue

                    cafeteria = cafeteria_names[idx]

                    # 메뉴 텍스트 추출
                    menu_html = col.find("p")
                    if menu_html:
                        menu_text = menu_html.get_text(separator="\n", strip=True)
                    else:
                        menu_text = col.get_text(strip=True)

                    # 운영하지 않는 경우 제외
                    if any(skip_word in menu_text for skip_word in ["운영안함", "메뉴운영내역", "준비중"]):
                        continue

                    if not menu_text.strip():
                        continue

                    # 메뉴 라인 정리
                    menu_lines = [line.strip() for line in menu_text.strip().split("\n") if line.strip()]

                    if menu_lines:  # 메뉴가 있는 경우만 추가
                        meals.append({
                            "meal_type": current_meal_type or "정보없음",
                            "target": current_target or "전체",
                            "cafeteria": cafeteria,
                            "menu": menu_lines
                        })

            result = {
                "status": "success",
                "date": date_str.replace(".", "-"),
                "meals": meals,
                "total_cafeterias": len(meals),
                "source": "충남대 모바일 식단표"
            }

            print(f"✅ {len(meals)}개 식당 메뉴 수집 완료")
            return result

        except Exception as e:
            print(f"❌ 식단 크롤링 오류: {e}")

    def fetch_latest_notices(self):
        print("📢 공지사항 크롤링 중...")

        try:
            # 기본 URL
            BASE_URL = "https://plus.cnu.ac.kr/_prog/_board/"

            # 요청 파라미터
            PARAMS = {
                "code": "sub07_0702",
                "site_dvs_cd": "kr",
                "menu_dvs_cd": "0702",
                "skey": "",
                "sval": "",
                "site_dvs": "",
                "ntt_tag": "",
                "GotoPage": 1
            }

            def get_notice_list(page=1):
                PARAMS["GotoPage"] = page
                response = requests.get(BASE_URL, params=PARAMS)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                # board_list 클래스의 div 객체 찾기
                board_div = soup.find('div', class_='board_list')
                if not board_div:
                    print("📛 'board_list' 클래스를 가진 div를 찾지 못했습니다.")
                    return []

                rows = board_div.find_all('tr')
                notices = []

                for row in rows[1:]:  # 첫 번째는 헤더
                    cols = row.find_all('td')
                    if len(cols) < 4:
                        continue

                    title_tag = cols[1].find('a')
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)

                    # 작성자
                    writer = cols[2].get_text(strip=True)

                    # 날짜
                    date = cols[3].get_text(strip=True)

                    notices.append({
                        'title': title,
                        'writer': writer,
                        'date': date
                    })

                return notices

            all_notices = []
            for page in range(1, 6):  # 예: 5페이지까지 크롤링
                notices = get_notice_list(page)
                if not notices:
                    break
                all_notices.extend(notices)

            print(f"총 {len(all_notices)}개의 게시물 수집 완료")
            return all_notices

        except Exception as e:
            print(f"❌ 공지사항 크롤링 오류: {e}")
            return [{
                "title": "공지사항을 가져올 수 없습니다.",
                "message": "인터넷 연결을 확인하고 충남대 홈페이지를 직접 방문하세요.",
                "url": self.urls["main_notice"]
            }]

    def normalize_date_format(self, date_input):
        """다양한 날짜 형식을 YYYY.MM.DD로 변환"""
        try:
            # 이미 올바른 형식인 경우
            if isinstance(date_input, str) and len(date_input) == 10 and "." in date_input:
                return date_input

            # date 객체인 경우
            if isinstance(date_input, date):
                return date_input.strftime("%Y.%m.%d")

            # 문자열 처리
            if isinstance(date_input, str):
                # "-" 구분자를 "."로 변경
                if "-" in date_input:
                    return date_input.replace("-", ".")

                # 기타 형식 처리
                date_input = date_input.replace("/", ".").replace(" ", "")

                # YYYY.M.D 형식을 YYYY.MM.DD로 변환
                parts = date_input.split(".")
                if len(parts) == 3:
                    year, month, day = parts
                    return f"{year}.{month.zfill(2)}.{day.zfill(2)}"

            # 파싱 실패 시 오늘 날짜
            return date.today().strftime("%Y.%m.%d")

        except Exception:
            return date.today().strftime("%Y.%m.%d")

    def search_comprehensive_info(self, question):
        """포괄적인 정보 검색 (정적 + 실시간)"""
        question_lower = question.lower()
        relevant_info = []

        # 졸업요건 관련
        if any(word in question_lower for word in ['졸업', '학점', '전공', '교양', '요건', '논문']):
            relevant_info.append(("졸업요건_정보", self.static_knowledge["graduation"]))

        # 공지사항 관련 (실시간 크롤링)
        if any(word in question_lower for word in ['공지', '장학금', '신청', '안내', '소식', '행사']):
            latest_notices = self.fetch_latest_notices()
            relevant_info.append(("최신공지", latest_notices))
            relevant_info.append(("공지사항_기본정보", self.static_knowledge["notice"]))

        # 학사일정 관련
        if any(word in question_lower for word in
               ['수강신청', '수강', '신청', '시험', '개강', '종강', '일정', '언제', '학사', '방학', '계절학기']):
            relevant_info.append(("학사일정_정보", self.static_knowledge["academic_schedule"]))

        # 식단 관련 (실시간 크롤링)
        if any(word in question_lower for word in ['식단', '학식', '메뉴', '식당', '밥', '점심', '저녁', '아침','1학','2학','3학','긱사','기숙']):
            relevant_info.append(("식당_기본정보", self.static_knowledge["dining"]))
            # 날짜 추출 시도
            date_str = self.extract_date_from_question(question)
            # 식단 크롤링 (날짜 자동 처리)
            today_menu = self.fetch_today_menu(date_str)
            relevant_info.append(("식단정보", today_menu))

        # 셔틀버스 관련
        if any(word in question_lower for word in ['셔틀', '버스', '교통', '시간표', '운행', '통학', '대전역', '유성']):
            relevant_info.append(("셔틀버스_정보", self.static_knowledge["shuttle"]))

        # 연락처 정보 (항상 포함)
        relevant_info.append(("연락처_정보", self.static_knowledge["contacts"]))

        return relevant_info


class CompleteCampusChatBot:
    """완전한 캠퍼스 챗봇 - AWQ 양자화 모델 사용"""

    def __init__(self, model_name = "Qwen/Qwen3-14B-AWQ"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"🖥️ 디바이스: {self.device}")
        print(f"🤖 모델: {model_name}")
        print("🔧 AWQ 4-bit 양자화 모델 사용")

        # 완전한 지식 베이스 초기화
        self.knowledge_base = CompleteCampusKnowledgeBase()
        print("📚 완전한 지식 베이스 로드 완료")

        # 모델 로드
        self.load_model()
        print("🤖 AWQ 챗봇 초기화 완료")

    def load_model(self):
        """AWQ 양자화 모델 로드"""
        try:
            print("🔄 AWQ 양자화 Qwen 모델 로딩 중...")

            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )

            # pad_token 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            # AWQ 모델 로드 (이미 양자화되어 있음)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            self.model.eval()
            print("✅ AWQ 모델 로딩 완료 (메모리 절약: ~70%)")

        except Exception as e:
            print(f"❌ AWQ 모델 로딩 실패: {e}")
            print("💡 AWQ 모델이 없을 수 있습니다. 일반 모델로 fallback 시도...")

            # Fallback to regular model
            try:
                fallback_model = "Qwen/Qwen2.5-7B-Instruct"
                print(f"🔄 {fallback_model}로 fallback 시도...")

                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model, trust_remote_code=True)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token

                self.model = AutoModelForCausalLM.from_pretrained(
                    fallback_model,
                    device_map="auto",
                    torch_dtype=torch.float16,
                    trust_remote_code=True
                )

                self.model_name = fallback_model
                print("✅ Fallback 모델 로딩 완료")

            except Exception as fallback_error:
                print(f"❌ Fallback 모델도 실패: {fallback_error}")
                raise

    def create_rich_context(self, relevant_info):
        """풍부한 컨텍스트 생성 (길이 최적화)"""
        context = "=== 충남대학교 종합 정보 ===\n\n"

        for info_type, info_data in relevant_info:
            context += f"【{info_type}】\n"

            if info_type == "최신공지" and isinstance(info_data, list):
                for i, notice in enumerate(info_data[:2], 1):  # 3개 → 2개로 축소
                    context += f"{i}. {notice.get('title', 'N/A')}\n"

            elif info_type == "오늘메뉴":
                if info_data.get('status') == "크롤링 성공":
                    context += f"날짜: {info_data['date']} ({info_data['day']}요일)\n"
                    if 'items' in info_data and info_data['items']:
                        context += f"메뉴: {', '.join(info_data['items'][:3])}\n"  # 5개 → 3개로 축소
                else:
                    context += f"상태: {info_data.get('message', '정보 없음')}\n"

            elif isinstance(info_data, dict):
                # 핵심 정보만 포함하도록 축소
                key_count = 0
                for key, value in info_data.items():
                    if key_count >= 3:  # 최대 3개 항목만
                        break
                    if isinstance(value, dict):
                        context += f"• {key}: {str(value)[:50]}...\n"  # 길이 제한
                    else:
                        context += f"• {key}: {str(value)[:100]}\n"  # 길이 제한
                    key_count += 1

            context += "\n"

            # 전체 컨텍스트 길이 제한
            if len(context) > 1500:  # 길이 제한 강화
                context = context[:1500] + "...\n"
                break

        return context

    def create_balanced_prompt(self, question, context):
        """메모리 효율적인 프롬프트 생성"""
        now = datetime.now()
        today = date.today()
        weekday = today.strftime('%A')

        # 간단한 시간 정보만
        current_context = f"현재: {now.strftime('%Y-%m-%d %H:%M')} ({weekday})"

        prompt = f""" /no think
                <|im_start|>system
                너는 충남대학교 학생이 궁금한 정보를 물어볼때 대답해주는 어시스턴트야. 
                다음 정보를 바탕으로 간결하고 정확한 답변을 자신감있게 해줘.
                날짜와 관련된 정보가 있으면 오늘 날짜와 비교해서 정보 가져와줘
                {current_context}
                {context}
                <|im_end|>
                <|im_start|>user
                {question}
                <|im_end|>
                <|im_start|>assistant
                """
        return prompt



    def generate_comprehensive_answer(self, question, max_new_tokens=30000):
        """메모리 최적화된 답변 생성"""
        try:
            print(f"🔍 질문 분석 중: {question}")

            # 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 1. 관련 정보 검색
            relevant_info = self.knowledge_base.search_comprehensive_info(question)

            # 2. 컨텍스트 생성 (크기 제한)
            context = self.create_rich_context(relevant_info)

            # 3. 프롬프트 생성
            prompt = self.create_balanced_prompt(question, context)

            # 4. 토크나이징 (길이 제한 강화)
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=3000  # 더 짧게 제한
            ).to(self.device)

            # 메모리 정리
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 5. 답변 생성 (메모리 절약 설정)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,  # 더 짧게 제한
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )

            # 즉시 메모리 해제
            del inputs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 6. 디코딩
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

            # 메모리 해제
            del outputs
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # 7. 답변 추출 (프롬프트와 특수 토큰 제거)
            answer = self.extract_answer_from_response(full_response, prompt)

            # 8. 답변 품질 검사
            if not answer or len(answer) < 5:
                return self.get_fallback_answer(question)

            print("✅ 답변 생성 완료")
            return answer

        except torch.cuda.OutOfMemoryError:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("❌ GPU 메모리 부족 - Fallback 사용")
            return self.get_fallback_answer(question)

        except Exception as e:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print(f"❌ 답변 생성 오류: {e}")
            return self.get_fallback_answer(question)

    def extract_answer_from_response(self, full_response, prompt):
        """응답에서 실제 답변 부분만 추출 - 개선된 버전"""
        try:
            # 1. 먼저 <think> 태그와 내용 완전 제거
            import re
            answer = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL)

            # 2. /no think 제거
            answer = re.sub(r'/no think\s*', '', answer)

            # 3. 시스템 프롬프트 부분 제거
            if "너는 충남대학교 학생이 궁금한 정보를 물어볼때 대답해주는 어시스턴트야" in answer:
                # assistant 이후 부분만 추출
                parts = answer.split("assistant")
                if len(parts) > 1:
                    answer = parts[-1].strip()

            # 4. 특수 토큰들 제거
            answer = re.sub(r'<\|im_end\|>', '', answer)
            answer = re.sub(r'<\|im_start\|>.*?>', '', answer)

            # 5. system, user, assistant 태그들 제거
            answer = re.sub(r'\n\s*(system|user|assistant)\s*\n', '\n', answer)
            answer = re.sub(r'^(system|user|assistant)\s*', '', answer)

            # 6. 컨텍스트 정보 제거
            if "=== 충남대학교 종합 정보 ===" in answer:
                parts = answer.split("assistant")
                if len(parts) > 1:
                    answer = parts[-1].strip()

            # 7. 프롬프트에서 사용자 질문 추출하여 답변에서 제거
            if "user" in prompt and "assistant" in prompt:
                # 사용자 질문 부분 찾기
                user_parts = prompt.split("user")
                if len(user_parts) > 1:
                    assistant_parts = user_parts[-1].split("assistant")
                    if len(assistant_parts) > 0:
                        user_question = assistant_parts[0].strip()
                        # 답변에서 사용자 질문 제거
                        if user_question in answer:
                            answer = answer.replace(user_question, "").strip()

            # 8. 최종 정리
            answer = answer.strip()

            # 9. 여전히 시스템 텍스트가 남아있는지 확인
            unwanted_patterns = [
                r'현재: \d{4}-\d{2}-\d{2} \d{2}:\d{2} \([^)]+\)',
                r'【[^】]*】[^【]*',  # 【】로 둘러싸인 섹션들
                r'• [^:]+: [^•]*',  # • 로 시작하는 정보들
            ]

            for pattern in unwanted_patterns:
                answer = re.sub(pattern, '', answer, flags=re.DOTALL)

            # 10. 빈 줄 정리
            answer = re.sub(r'\n\s*\n\s*\n', '\n\n', answer)
            answer = answer.strip()

            # 11. 최종 검증 - 답변이 너무 짧거나 시스템 정보만 있는 경우
            if not answer or len(answer.strip()) < 10:
                return None

            # 12. 시스템 정보가 여전히 남아있는 경우 간단한 답변으로 대체
            if any(keyword in answer for keyword in ['충남대학교 종합 정보', '현재:', '【', '•']):
                return None

            return answer

        except Exception as e:
            print(f"⚠️ 답변 추출 중 오류: {e}")
            return None

    #나중확인
    def get_fallback_answer(self, question):
        """간단한 Fallback 답변 (메모리 절약)"""
        question_lower = question.lower()

        if any(word in question_lower for word in ['셔틀', '버스']):
            return """🚌 2025년 충남대 셔틀버스 안내

📍 교내순환: 08:30~17:30 (1일 10회)
시간: 08:30, 09:30, 09:40, 10:30, 11:30, 13:30, 14:30, 15:30, 16:30, 17:30

📍 등교전용: 월평역 08:20 출발 → 정심화 국제문화회관
📍 캠퍼스순환: 08:10 대덕 출발 → 08:50 보운 도착

📞 문의: 총무과 042-821-5114"""

        elif any(word in question_lower for word in ['졸업', '학점']):
            return "충남대학교 졸업요건은 130학점 이상입니다. 공학계열은 140학점이 필요합니다. 자세한 문의: 학사지원과 042-821-5025"

        elif any(word in question_lower for word in ['식단', '메뉴']):
            return "학생식당: 한식 4,000원, 양식 5,000원. 운영시간: 11:30-14:00, 17:30-19:00. 생협: 042-821-5890"

        else:
            return "문의사항은 관련 부서로 연락주세요. 학사지원과 042-821-5025, 총무과 042-821-5114"

    def process_test_file(self, test_file_path, output_file_path):
        """개별 처리로 메모리 절약"""
        try:
            if not os.path.exists(test_file_path):
                print(f"❌ 테스트 파일이 없습니다: {test_file_path}")
                return False

            with open(test_file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)

            results = []
            print(f"📝 AWQ 모델 개별 처리 중... (총 {len(test_data)}개)")

            for i, item in enumerate(test_data):
                try:
                    print(f"🔄 {i+1}/{len(test_data)}: {item['user'][:30]}...")

                    # 각 질문마다 메모리 정리
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    answer = self.generate_comprehensive_answer(item['user'])

                    results.append({
                        "user": item['user'],
                        "model": answer
                    })

                    # 5개마다 중간 저장 및 메모리 정리
                    if (i + 1) % 3 == 0:
                        print(f"💾 중간 저장... ({i+1}개 완료)")
                        self.save_partial_results(results, output_file_path)
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                except Exception as e:
                    print(f"❌ 질문 {i+1} 실패: {e}")
                    results.append({
                        "user": item['user'],
                        "model": f"처리 실패: {str(e)}"
                    })
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

            # 최종 저장
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            print(f"✅ AWQ 모델 결과 저장 완료: {output_file_path}")
            return True

        except Exception as e:
            print(f"❌ 테스트 파일 처리 중 오류: {e}")
            return False

    def save_partial_results(self, results, output_file_path):
        """부분 결과 저장"""
        try:
            os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 중간 저장 실패: {e}")

    def chat_interactive(self):
        """대화형 채팅"""
        print("\n🤖 충남대 AWQ 양자화 RAG 챗봇입니다!")
        print("📡 실시간 정보 크롤링이 포함되어 있습니다.")
        print("(종료: 'quit' 또는 'exit')")

        while True:
            try:
                user_input = input("\n👤 질문: ").strip()

                if user_input.lower() in ['quit', 'exit', '종료']:
                    print("👋 이용해주셔서 감사합니다!")
                    break

                if not user_input:
                    continue

                print("🔍 정보 검색 및 답변 생성 중...")
                answer = self.generate_comprehensive_answer(user_input)
                print(f"🤖 답변: {answer}")

            except KeyboardInterrupt:
                print("\n👋 이용해주셔서 감사합니다!")
                break


def main():
    """메인 함수"""
    print("🎓 충남대 Campus RAG ChatBot (AWQ 양자화)")
    print("📡 실시간 크롤링 + 정적 정보 + AWQ 4-bit 양자화")
    print("🔧 메모리 최적화 버전")
    print("=" * 60)

    try:
        # AWQ 양자화 RAG 챗봇 초기화
        chatbot = CompleteCampusChatBot(
            model_name = "Qwen/Qwen3-14B-AWQ"
        )

        # 테스트 파일 처리
        test_file_path = "./data/test_chat.json"
        output_file_path = "./outputs/chat_output.json"

        if os.path.exists(test_file_path):
            print(f"📂 테스트 파일 발견: {test_file_path}")
            success = chatbot.process_test_file(test_file_path, output_file_path)

            if success:
                print("✅ AWQ 양자화 챗봇 테스트 완료!")

                # 결과 미리보기
                with open(output_file_path, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                print("\n📋 결과 미리보기 (처음 3개):")
                for i, result in enumerate(results[:3]):
                    print(f"\n{i + 1}. 질문: {result['user']}")
                    print(f"   답변: {result['model']}")
                    print("-" * 60)

                # 모델 정보 출력
                print(f"\n🤖 사용된 모델: {chatbot.model_name}")
                print(f"🔧 양자화: AWQ 4-bit")
                print(f"🖥️ 실행 디바이스: {chatbot.device}")
                print(f"💾 예상 메모리 절약: 70%")

            else:
                print("❌ 테스트 실패!")
        else:
            print(f"⚠️ 테스트 파일이 없습니다: {test_file_path}")

    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        print("💡 AWQ 모델이 없거나 GPU 메모리 부족일 수 있습니다")
        print("💡 fallback 모델로 자동 전환됩니다")


if __name__ == "__main__":
    main()