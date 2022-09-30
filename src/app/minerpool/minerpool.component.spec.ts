import { ComponentFixture, TestBed } from '@angular/core/testing';

import { MinerpoolComponent } from './minerpool.component';

describe('MinerpoolComponent', () => {
  let component: MinerpoolComponent;
  let fixture: ComponentFixture<MinerpoolComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ MinerpoolComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(MinerpoolComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
