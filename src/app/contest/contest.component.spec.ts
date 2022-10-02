import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ContestComponent } from './contest.component';
import {ActivatedRoute} from "@angular/router";
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('ContestComponent', () => {
  let component: ContestComponent;
  let fixture: ComponentFixture<ContestComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ContestComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ContestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
