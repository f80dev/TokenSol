import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BuildOpeComponent } from './build-ope.component';
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {RouterTestingModule} from "@angular/router/testing";
import {HttpClientModule} from "@angular/common/http";

describe('BuildOpeComponent', () => {
  let component: BuildOpeComponent;
  let fixture: ComponentFixture<BuildOpeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ BuildOpeComponent ],
      imports: [MatSnackBarModule,RouterTestingModule,HttpClientModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BuildOpeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
